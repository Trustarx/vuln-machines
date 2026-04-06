# Vuln Machines

Intentionally vulnerable Docker targets for pentesting practice.

> ⚠️ **FOR EDUCATIONAL USE ONLY** — run locally or on an isolated network. Never expose to the internet.

## Machines

| Machine | Focus | Port |
|---------|-------|------|
| [privesc-lab](./privesc-lab/) | Command injection → Linux privilege escalation | 8080, 2222 |
| [api-lab](./api-lab/) | REST API vulns: IDOR, mass assignment, JWT, SQLi | 3000 |

## Quick Start

Each machine is self-contained. From any machine directory:

```bash
docker compose up --build -d
```

## Stopping

```bash
docker compose down
```
