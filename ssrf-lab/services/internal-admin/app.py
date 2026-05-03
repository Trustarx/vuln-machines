"""
PaperPress Internal Admin Panel
================================
Lives on the internal docker network only — accessible at `admin.internal`.
Trusts the X-Forwarded-For header for "intranet authentication".

VULN: any request that arrives over HTTP gets to set X-Forwarded-For,
so an SSRF chain like
    /api/render?url=http://admin.internal/admin/flag
will be authenticated as "internal" and return the flag.

Bonus secondary path: the panel exposes /admin/exec which runs a whitelisted
set of "diagnostic" commands. The whitelist regex is sloppy so command
injection is possible if the user finds it.
"""

from flask import Flask, request, jsonify, Response
import subprocess
import re

app = Flask(__name__)


def is_internal(req) -> bool:
    """Naive 'is the caller internal?' check.

    Trusts the X-Forwarded-For header if it claims a private RFC1918 address,
    OR if there's no XFF header (assumes the only direct callers are the
    intranet load balancer). Both are wrong:
      - SSRF in the public web service can hit us directly with no XFF
        and we'll authenticate it.
      - The XFF check is just substring / startswith, so an attacker can
        forge it from outside if they ever break the front door.
    """
    xff = req.headers.get("X-Forwarded-For", "")
    if not xff:
        # No XFF == direct call from inside the container network.
        return True
    # If the XFF claims an internal IP, trust it (BAD!)
    return (xff.startswith("10.") or
            xff.startswith("192.168.") or
            xff.startswith("172.") or
            xff == "127.0.0.1")


@app.route("/")
def root():
    if not is_internal(request):
        return "Forbidden — internal users only\n", 403
    return ("PaperPress — Internal Admin v1.2\n"
            "Endpoints:\n"
            "  GET  /admin/users\n"
            "  GET  /admin/flag\n"
            "  POST /admin/exec   (diagnostics)\n")


@app.route("/admin/users")
def users():
    if not is_internal(request):
        return "Forbidden\n", 403
    return jsonify([
        {"id": 1, "user": "admin",  "email": "admin@paperpress.local",  "role": "owner"},
        {"id": 2, "user": "alice",  "email": "alice@paperpress.local",  "role": "editor"},
        {"id": 3, "user": "bob",    "email": "bob@paperpress.local",    "role": "viewer"},
        {"id": 4, "user": "render", "email": "render@paperpress.local", "role": "service"},
    ])


@app.route("/admin/flag")
def flag():
    if not is_internal(request):
        return "Forbidden\n", 403
    return ("FLAG{ssrf_pivoted_to_internal_admin_panel}\n"
            "Nice. The X-Forwarded-For 'auth' was bypassed because the SSRF\n"
            "request from the renderer arrived without any XFF header — and\n"
            "this service treats that as an intranet caller.\n")


# --- bonus injection path -----------------------------------------------

ALLOWED_CMDS = re.compile(r"^(uptime|whoami|ls|cat /etc/hostname)\b")


@app.route("/admin/exec", methods=["POST"])
def exec_cmd():
    if not is_internal(request):
        return "Forbidden\n", 403
    cmd = request.form.get("cmd", "")
    # VULN: regex anchors only the start; backtick / semicolon / && injection works
    if not ALLOWED_CMDS.match(cmd):
        return jsonify(error="command not whitelisted"), 400
    out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
    return Response(out.stdout + out.stderr, mimetype="text/plain")


@app.route("/health")
def health():
    return "ok\n"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=False)
