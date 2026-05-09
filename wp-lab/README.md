# wp-lab — WordPress xmlrpc brute → plugin upload RCE

A realistic multi-step WordPress engagement. The target is a vanilla
WordPress 5.8 site ("MidwestRealty Properties") with three users and
default-enabled `xmlrpc.php`. The chain teaches:

1. **Recon** — fingerprint WordPress, identify version
2. **User enumeration** — REST API (`/wp-json/wp/v2/users`) and the
   `?author=N` redirect leak
3. **xmlrpc.php discovery** — `system.listMethods` shows
   `wp.getUsersBlogs` and `system.multicall` exposed
4. **Multicall amplification fails** — WP 4.4+ patched the classic
   amplification trick (every entry returns the same `403`)
5. **Single-request brute-force still works** — no rate limiting on
   `wp.getUsersBlogs`, weak admin password (`Welcome123!`) cracks
   from a top-100 list
6. **Authenticated plugin upload** — admin can install zip plugins;
   pack a 3-line PHP webshell, upload, activate
7. **RCE → flag** — `cat /flag.txt` from `www-data`

## Run

```bash
docker compose up -d --build
```

Public site at `http://localhost:8091`. First start takes ~30s while
the init script installs WordPress, creates the users, sets pretty
permalinks, and publishes one post per user (so they all appear in the
REST API enumeration).

## Lab properties

- WordPress 5.8.x with default config (xmlrpc enabled, REST API
  unauthenticated, mod_rewrite + AllowOverride All)
- MariaDB 10.5 sidecar
- Three users: `admin:Welcome123!`, `bob:bob123`, `editor:Spring2024!`
- Flag baked into the image at `/flag.txt`, world-readable
- Hint file at `wp-content/uploads/.notes.txt` for users who poke
  around with the webshell

## Goal

Read `/flag.txt`. The flag is `FLAG{wp_xmlrpc_brute_to_plugin_rce_chain}`.

## Solution

See [`SOLUTION.md`](./SOLUTION.md) for the full walkthrough including
Python snippets and the exact curl commands.
