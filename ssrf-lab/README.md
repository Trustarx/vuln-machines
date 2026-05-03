# ssrf-lab — PaperPress Document Rendering

Server-Side Request Forgery training lab. A "PDF rendering" service fetches
arbitrary URLs server-side, with a naive blacklist filter. SSRF allows
pivoting to a mock AWS EC2 metadata service (IAM credentials), and to an
internal admin panel that trusts request-headers for auth.

## Run

```bash
docker compose up -d --build
```

Public service on `http://localhost:8090`. The metadata service and admin
panel are reachable only via SSRF through the renderer.

## What's in scope

- **SSRF blacklist bypass** — string-based filter is trivially defeated
  by docker DNS hostnames or `0.0.0.0`
- **AWS IMDSv1 simulation** — pulls IAM credentials, instance metadata, and
  cloud-init user-data
- **Internal admin pivot** — `X-Forwarded-For`-based auth that breaks when
  the SSRF request arrives without XFF

## Goal

Two flags:
1. `FLAG{ssrf_to_imds_metadata_pwned}` — from the AWS metadata service
2. `FLAG{ssrf_pivoted_to_internal_admin_panel}` — from the internal admin

## Solution

See [`SOLUTION.md`](./SOLUTION.md) for the full walkthrough.
