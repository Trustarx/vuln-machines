# Vuln Machines

Intentionally vulnerable Docker targets for pentesting practice.

> ⚠️ **FOR EDUCATIONAL USE ONLY** — run locally or on an isolated network. Never expose to the internet.

## Machines

| Machine | Focus | Ports |
|---------|-------|-------|
| [privesc-lab](./privesc-lab/) | Command injection → Linux privilege escalation (6 vectors) | 8080, 2222 |
| [api-lab](./api-lab/) | REST API: IDOR, mass assignment, JWT alg:none, weak secret, broken auth, SQLi | 3000 |
| [msf-lab](./msf-lab/) | Metasploit practice: vsftpd 2.3.4 backdoor, Shellshock CGI, distcc RCE | 2121, 6200, 8888, 3632 |
| [crypto-lab](./crypto-lab/) | JWT weak secret, alg:none, OAuth open redirect, AES-ECB cookie forgery | 5001 |

## Quick Start

Each machine is self-contained. From any machine directory:

```bash
docker compose up --build -d
```

To run all machines at once:

```bash
for dir in privesc-lab api-lab msf-lab crypto-lab; do
  (cd $dir && docker compose up --build -d)
done
```

## Machine Details

### privesc-lab — `http://localhost:8080`
Entry via command injection in a Flask web app. Six privesc paths to root:
- SUID `find`, writable cron job, `sudo vim`, writable `/etc/passwd`, readable root SSH key, `CAP_SETUID` on python3

SSH access: `ssh webuser@localhost -p 2222` (password: `websecure123`)

### api-lab — `http://localhost:3000`
REST API built with Node.js/Express + SQLite. Vulnerabilities:
- IDOR on `/api/users/:id` and `/api/users/:id/notes`
- Mass assignment via `PUT /api/users/:id` (set `role: "admin"`)
- JWT alg:none bypass + weak HS256 secret (`secret`)
- Broken admin check — any valid token reaches `/api/admin/flag`
- SQLi in `GET /api/products/search?q=`

### msf-lab — Multi-port
Three Metasploit reverse shell vectors:

| Exploit | MSF Module | Port |
|---------|-----------|------|
| vsftpd 2.3.4 backdoor | `exploit/unix/ftp/vsftpd_234_backdoor` | 2121 (shell on 6200) |
| Shellshock CGI | `exploit/multi/http/apache_mod_cgi_bash_env_exec` | 8888 |
| distcc RCE | `exploit/unix/misc/distcc_exec` | 3632 |

### crypto-lab — `http://localhost:5001`
Simulated company internal portal (AcmeCorp v2.3). Vulnerabilities:
- JWT HS256 weak secret (`corp2024`) — crack with hashcat: `hashcat -a 0 -m 16500 <jwt> rockyou.txt`
- JWT alg:none — forge admin token with no signature
- JWT role claim trusted from token — change `"role":"admin"` to escalate
- OAuth open redirect — `redirect_uri` validated with `startswith()` only
- OAuth missing state — CSRF on the OAuth flow
- AES-ECB encrypted session cookie — block replay to forge admin role
- `/api/debug` leaks cipher mode and key length

## Stopping

```bash
# Stop a single machine
cd <machine-dir> && docker compose down

# Stop all
for dir in privesc-lab api-lab msf-lab crypto-lab; do
  (cd $dir && docker compose down)
done
```
