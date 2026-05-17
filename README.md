# Vuln Machines

Intentionally vulnerable Docker targets for pentesting practice — built and maintained by Trustarx.

> ⚠️ **FOR EDUCATIONAL USE ONLY** — run locally or on an isolated network. Never expose to the internet.

Each lab is a self-contained Docker Compose stack. Every lab folder contains a `SOLUTION.md` with full step-by-step exploitation instructions.

---

## Machines at a glance

| Machine | Focus | Difficulty | Ports |
|---|---|---|---|
| [privesc-lab](./privesc-lab/) | Command injection → 6 Linux privesc vectors | Easy–Medium | 8080, **2223** (SSH) |
| [api-lab](./api-lab/) | REST API: IDOR, mass assignment, JWT, SQLi | Medium | 3000 |
| [msf-lab](./msf-lab/) | Metasploit practice: vsftpd, Shellshock, distcc | Easy | **2122** (FTP), 6200, 8888, 3632 |
| [crypto-lab](./crypto-lab/) | JWT alg:none/weak secret, AES-ECB, OAuth | Medium–Hard | 5001 |
| [ftp-lab](./ftp-lab/) | Anonymous FTP → ProFTPD `mod_copy` (CVE-2015-3306) → root | Medium | 2121, 8081, 2222 (SSH) |
| [sqli-lab](./sqli-lab/) | Referrer bypass + time-based blind SQLi (PHP/MySQL) | Medium | 8082 |
| [ssrf-lab](./ssrf-lab/) | SSRF blacklist bypass → AWS IMDS metadata + internal admin pivot | Medium | 8090 |
| [grafana-lab](./grafana-lab/) | CVE-2021-43798 path traversal → leak grafana.ini → admin login → flag | Easy–Medium | 3001 |
| [spa-lab](./spa-lab/) | JS source analysis: hardcoded secrets, source maps, debug endpoints, JWT forge | Easy | 8093 |
| [wp-lab](./wp-lab/) | WordPress: user enum + xmlrpc brute → plugin upload RCE | Medium | 8091 |

> **Port allocation note:** ports were chosen to avoid collisions when running all six labs simultaneously. ftp-lab owns FTP/2121 and SSH/2222; the others have been moved to 2122 (msf-lab FTP) and 2223 (privesc-lab SSH).

---

## Quick start

```bash
# Single lab
cd <machine-dir>
docker compose up -d --build

# All six at once
for dir in privesc-lab api-lab msf-lab crypto-lab ftp-lab sqli-lab ssrf-lab wp-lab; do
  (cd $dir && docker compose up -d --build)
done
```

To run on a LAN-accessible machine and let teammates connect, set `MASQ_ADDR` for ftp-lab so PASV advertises the right IP:
```bash
MASQ_ADDR=10.0.1.50 docker compose -f ftp-lab/docker-compose.yml up -d
```

---

## Machine details

### 1. privesc-lab — `http://<target>:8080`
Linux privilege escalation training ground. You start with command injection in a Flask "ping" app and work your way to root via any of six independent vectors.

**Vulnerabilities:**
- Command injection in `/ping` (`shell=True` with unsanitised input)
- Information disclosure via `/debug`
- Six privesc paths to root: SUID `find`, writable cron, `sudo vim`, writable `/etc/passwd`, readable root SSH key, `CAP_SETUID` on python3

**Tools to practice:** Burp Suite, manual command injection, LinPEAS, GTFOBins  
**SSH:** `ssh webuser@<target> -p 2223` (password: `websecure123`)  
**Solution:** [`privesc-lab/SOLUTION.md`](./privesc-lab/SOLUTION.md)

---

### 2. api-lab — `http://<target>:3000`
Modern REST API security. Node.js/Express + SQLite. Built around OWASP API Top 10 issues.

**Vulnerabilities:**
- **IDOR** on `/api/users/:id` and `/api/users/:id/notes` — view any user's PII, password hash, API key
- **Mass assignment** via `PUT /api/users/:id` — set `role: "admin"` from a normal account
- **JWT alg:none** — forge unsigned admin tokens
- **JWT weak HS256 secret** (`secret`) — crack with hashcat in seconds
- **Broken admin check** — middleware only verifies token presence, not role
- **SQL injection** in `GET /api/products/search?q=` (SQLite, raw template literal)

**Tools to practice:** Burp, ffuf, hashcat (mode 16500), sqlmap, jwt_tool  
**Solution:** [`api-lab/SOLUTION.md`](./api-lab/SOLUTION.md)

---

### 3. msf-lab — Multi-port
Classic Metasploit-friendly machine with three independent RCE vectors. Great for first-time MSF users or for proving live exploits without writing custom code.

| Exploit | MSF Module | Port |
|---|---|---|
| vsftpd 2.3.4 backdoor (CVE-2011-2523) | `exploit/unix/ftp/vsftpd_234_backdoor` | 2122 (callback shell on 6200) |
| Shellshock CGI (CVE-2014-6271) | `exploit/multi/http/apache_mod_cgi_bash_env_exec` | 8888 |
| distcc RCE (CVE-2004-2687) | `exploit/unix/misc/distcc_exec` | 3632 |

**Tools to practice:** msfconsole, nmap NSE scripts, manual netcat triggers  
**Solution:** [`msf-lab/SOLUTION.md`](./msf-lab/SOLUTION.md)

---

### 4. crypto-lab — `http://<target>:5001`
"AcmeCorp Internal Portal v2.3" — a Python/Flask app demonstrating real-world JWT, AES, and OAuth flaws.

**Vulnerabilities:**
- **JWT alg:none** — `decode_jwt()` skips signature verification when alg is `"none"`
- **JWT weak HS256 secret** (`corp2024`) — crack with hashcat
- **Role claim from token** — payload's `role` claim is trusted as authoritative
- **OAuth open redirect** — `redirect_uri` validated only with `startswith()`
- **OAuth missing state** — CSRF in the auth code grant flow
- **AES-128-ECB session cookie** — `session_role=AES_ECB(user=...|role=...|dept=...)` susceptible to block-swap forgery
- **/api/debug** leaks `jwt_algo`, `aes_mode: ECB`, `aes_keylen: 128`
- **IDOR** on `/api/users/<id>`

**Tools to practice:** jwt_tool, hashcat (16500), pycryptodome, Burp Repeater for ECB block manipulation  
**Solution:** [`crypto-lab/SOLUTION.md`](./crypto-lab/SOLUTION.md)

---

### 5. ftp-lab — Anonymous FTP + ProFTPD mod_copy (CVE-2015-3306)
Realistic chained attack. Anonymous FTP leaks the next-stage credentials, which unlock ProFTPD's `mod_copy` module to plant a PHP webshell in the Apache web root, leading to a www-data shell — then privesc to root.

**Vulnerabilities:**
- Anonymous FTP read on `/var/ftp/pub` containing a leaked `config.bak` with cleartext credentials
- ProFTPD `mod_copy` enabled (SITE CPFR / SITE CPTO) — server-side file copy as authenticated user
- ftpuser is in the `www-data` group, web root is group-writable → write a PHP shell into `/var/www/html`
- Writable cron script (`/opt/maintenance/cleanup.sh`) runs as root every minute
- `ftpuser ALL=(root) NOPASSWD: /usr/bin/vim` — sudo misconfig

**Network notes:** PASV uses port range `60000-60100`. If running on a LAN, set `MASQ_ADDR=<host-ip>` before `docker compose up`.

**Tools to practice:** ftp/lftp, Burp/curl, Metasploit (`exploit/unix/ftp/proftpd_modcopy_exec`), GTFOBins for vim sudo  
**Solution:** [`ftp-lab/SOLUTION.md`](./ftp-lab/SOLUTION.md)

---

### 6. sqli-lab — `http://<target>:8082`
PHP + MySQL portal ("OutForm Letter Services") protected by a referrer-based access control. The referrer requirement is leaked in a browser `console.log`, and the protected page contains a clean time-based blind SQLi point that leads to cleartext admin credentials.

**Vulnerabilities:**
- Referrer-based access control on every page; required referrer leaked via `console.log` in the 403 response (visible in DevTools, **not** rendered on the page)
- Time-based blind SQL injection on `?id=` (integer interpolation, single-row query → exactly one `SLEEP()` per request)
- Cleartext password storage in the `users` table

**Tools to practice:** Burp Suite (Referer header tampering), DevTools console, sqlmap (with `--referer`), or hand-rolled Python extraction script  
**Solution:** [`sqli-lab/SOLUTION.md`](./sqli-lab/SOLUTION.md)

---

### 7. ssrf-lab — `http://<target>:8090`
"PaperPress Document Rendering" — a Flask service that fetches a user-supplied URL server-side. Three-service lab: the public renderer plus a mock AWS EC2 metadata service and an internal admin panel, both reachable only via SSRF.

**Vulnerabilities:**
- **SSRF** in `/api/render?url=` with a substring-based blacklist (blocks `127.0.0.1`, `localhost`, `169.254.169.254`)
- **Bypass via docker DNS** — internal hostnames `metadata`, `aws-metadata.internal`, `admin`, `admin.internal` aren't in the blacklist
- **AWS IMDSv1 simulation** — leaks IAM role credentials and cloud-init user-data (DB password, admin API key)
- **Header-trust auth** — the internal admin panel trusts `X-Forwarded-For` claiming an RFC1918 address, AND any request with no XFF (which is exactly what an SSRF-driven request looks like)
- **Bonus:** regex-based command whitelist on `/admin/exec` is anchored only at the start → shell injection via `;` / `&&`

**Tools to practice:** Burp Repeater (URL fuzzing), curl, awareness of cloud metadata services, AWS CLI with stolen creds  
**Solution:** [`ssrf-lab/SOLUTION.md`](./ssrf-lab/SOLUTION.md)

---

### 8. wp-lab — `http://<target>:8091`
"MidwestRealty Properties" — a stock WordPress 5.8 site with three users and the kind of config that bites real-world deployments. Multi-step engagement that mirrors the typical WPScan → Burp → Metasploit kill chain.

**Vulnerabilities:**
- **User enumeration** via `/wp-json/wp/v2/users/` (returns slug, display name) and the `?author=N` redirect leak
- **`xmlrpc.php` enabled** with no rate limiting — `wp.getUsersBlogs` is a clean login oracle
- **`system.multicall` amplification mitigation** — WP 4.4+ patched the classic batched-attempts trick. The lab teaches you to recognise the patch and fall back to single requests
- **Weak admin password** (`Welcome123!`) — top-1000 list, crackable in seconds
- **Authenticated plugin upload** — any admin can upload a zip plugin, which runs PHP under `www-data`. A 3-line PHP shell + `zip` is the entire payload
- **Flag** at `/flag.txt`, readable once you have a webshell

**Tools to practice:** WPScan (`-e u`, `--passwords rockyou.txt`), Burp Suite (form replay), Metasploit (`exploit/unix/webapp/wp_admin_shell_upload`), or hand-rolled Python  
**Solution:** [`wp-lab/SOLUTION.md`](./wp-lab/SOLUTION.md)

---

## Stopping

```bash
# Single lab
cd <machine-dir> && docker compose down

# All
for dir in privesc-lab api-lab msf-lab crypto-lab ftp-lab sqli-lab ssrf-lab wp-lab; do
  (cd $dir && docker compose down)
done
```

---

## Repository layout
```
vuln-machines/
├── README.md                ← this file
├── privesc-lab/
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── app.py
│   ├── setup-vulns.sh
│   └── SOLUTION.md
├── api-lab/                 ← Node.js REST API + SQLite
├── msf-lab/                 ← Python services simulating classic CVEs
├── crypto-lab/              ← Flask app: JWT/OAuth/AES-ECB
├── ftp-lab/                 ← ProFTPD + Apache + SSH
├── sqli-lab/                ← PHP + MySQL (OutForm portal)
├── ssrf-lab/                ← Flask + mock AWS IMDS + internal admin (PaperPress)
└── wp-lab/                  ← WordPress 5.8 + MariaDB (MidwestRealty Properties)
```

Every lab folder contains its own Dockerfile, compose file, source, setup scripts, and a step-by-step `SOLUTION.md` for the team.

---

## Maintainer notes

- All ports were chosen to avoid collisions when running every lab simultaneously — see the table at the top.
- Solutions are **not obfuscated** — these are training labs, not CTF challenges. The `SOLUTION.md` files are the canonical reference for what each machine teaches.
- If you find a lab where the documented solution path no longer works (e.g. a SLEEP payload that doesn't sleep, or a directory listing that doesn't list), open an issue — the lab is broken, not the test.
