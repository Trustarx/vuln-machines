"""
AcmeCorp Internal Portal v2.3
-------------------------------
FOR EDUCATIONAL / PENTESTING PRACTICE ONLY.

Intentional vulnerabilities:
  1. JWT weak secret   - HS256 signed with "corp2024", easily cracked
  2. JWT alg:none      - Server accepts unsigned tokens
  3. JWT role tampering- role claim trusted from token with no server-side check
  4. OAuth open redirect- redirect_uri only checked via startswith(), bypassable
  5. OAuth missing state- CSRF on the OAuth flow
  6. AES-ECB cookie    - Role encoded in ECB-encrypted cookie, block-replayable
  7. Info disclosure   - /api/debug leaks keys and config
"""

from flask import Flask, request, jsonify, redirect, render_template_string, make_response
import jwt as pyjwt
import json, base64, time, os, secrets
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

app = Flask(__name__)

# ── VULN 1 & 2: Weak JWT secret + alg:none accepted ──────────
JWT_SECRET = "corp2024"

# ── VULN 6: Hardcoded AES key, ECB mode (no IV) ──────────────
AES_KEY = b"AcmeCorp2019Key!"   # 16 bytes

# ── In-memory stores ─────────────────────────────────────────
USERS = {
    1: {"id": 1, "username": "admin",   "password": "Adm1n@corp2024", "role": "admin",  "email": "admin@acmecorp.local",   "dept": "IT"},
    2: {"id": 2, "username": "alice",   "password": "alice123",       "role": "user",   "email": "alice@acmecorp.local",   "dept": "Finance"},
    3: {"id": 3, "username": "bob",     "password": "bob456",         "role": "user",   "email": "bob@acmecorp.local",     "dept": "HR"},
    4: {"id": 4, "username": "charlie", "password": "charlie789",     "role": "manager","email": "charlie@acmecorp.local", "dept": "Engineering"},
}
USERS_BY_NAME = {u["username"]: u for u in USERS.values()}
REGISTERED   = {}   # username -> user dict (for newly registered users)

OAUTH_CODES  = {}   # code  -> {"user_id": ..., "expires": ...}
OAUTH_TOKENS = {}   # token -> {"user_id": ..., "scope": ...}

OAUTH_CLIENTS = {
    "acme-internal": {
        "name":          "AcmeCorp Portal",
        "secret":        "cl13nt-s3cr3t-2019",
        # VULN 4: redirect_uri validated only with startswith()
        "redirect_uris": ["http://localhost:3000/oauth/callback"],
    }
}

# ── Crypto helpers ────────────────────────────────────────────

def _pad(data: bytes) -> bytes:
    n = 16 - (len(data) % 16)
    return data + bytes([n] * n)

def _unpad(data: bytes) -> bytes:
    return data[: -data[-1]]

def ecb_encrypt(plaintext: str) -> str:
    """VULN: ECB mode — identical plaintext blocks → identical ciphertext blocks."""
    raw = _pad(plaintext.encode())
    c = Cipher(algorithms.AES(AES_KEY), modes.ECB(), backend=default_backend())
    ct = c.encryptor().update(raw)
    return base64.urlsafe_b64encode(ct).decode()

def ecb_decrypt(token: str) -> str:
    ct = base64.urlsafe_b64decode(token + "==")
    c = Cipher(algorithms.AES(AES_KEY), modes.ECB(), backend=default_backend())
    pt = c.decryptor().update(ct)
    return _unpad(pt).decode()

def make_jwt(payload: dict) -> str:
    return pyjwt.encode(payload, JWT_SECRET, algorithm="HS256")

def decode_jwt(token: str) -> dict | None:
    """VULN: accepts alg:none — no signature verification for unsigned tokens."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        raw_header = parts[0] + "=" * (-len(parts[0]) % 4)
        header = json.loads(base64.urlsafe_b64decode(raw_header))

        raw_payload = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(raw_payload))

        alg = header.get("alg", "HS256").lower()
        if alg == "none":
            # VULN: skip verification entirely
            return payload

        # HS256 path — uses weak JWT_SECRET
        return pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception:
        return None

def jwt_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        token = auth.replace("Bearer ", "").strip()
        if not token:
            token = request.cookies.get("jwt_token", "")
        payload = decode_jwt(token)
        if not payload:
            return jsonify({"error": "Unauthorized — provide a valid JWT"}), 401
        request.jwt_payload = payload
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        token = auth.replace("Bearer ", "").strip()
        if not token:
            token = request.cookies.get("jwt_token", "")
        payload = decode_jwt(token)
        if not payload:
            return jsonify({"error": "Unauthorized"}), 401
        # VULN 3: role is read directly from JWT — never cross-checked server-side
        if payload.get("role") != "admin":
            return jsonify({"error": "Forbidden — admins only"}), 403
        request.jwt_payload = payload
        return fn(*args, **kwargs)
    return wrapper

# ── HTML templates ────────────────────────────────────────────

INDEX_HTML = """<!DOCTYPE html>
<html>
<head><title>AcmeCorp Internal Portal</title>
<style>
  body{font-family:sans-serif;background:#f4f6f9;display:flex;justify-content:center;padding:60px}
  .card{background:#fff;padding:40px;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,.1);max-width:520px;width:100%}
  h1{color:#2c3e50;margin-top:0}h3{color:#7f8c8d}
  code{background:#eee;padding:2px 6px;border-radius:3px;font-size:13px}
  ul{line-height:2}a{color:#2980b9}
  .badge{display:inline-block;padding:2px 8px;border-radius:12px;font-size:12px;background:#e74c3c;color:#fff}
</style>
</head>
<body><div class="card">
  <h1>🏢 AcmeCorp Portal <span class="badge">v2.3</span></h1>
  <p>Welcome to the AcmeCorp internal employee portal. Please authenticate to continue.</p>
  <h3>API Endpoints</h3>
  <ul>
    <li><code>POST /api/auth/register</code> — create account</li>
    <li><code>POST /api/auth/login</code> — get JWT token</li>
    <li><code>GET  /api/profile</code> — your profile <em>[auth]</em></li>
    <li><code>GET  /api/users/&lt;id&gt;</code> — user lookup <em>[auth]</em></li>
    <li><code>GET  /api/payroll</code> — payroll data <em>[auth]</em></li>
    <li><code>GET  /api/admin/dashboard</code> — <strong>admin</strong></li>
    <li><code>GET  /api/admin/flag</code> — <strong>admin</strong></li>
    <li><code>GET  /oauth/authorize</code> — SSO login</li>
    <li><code>GET  /api/debug</code> — system debug</li>
  </ul>
  <h3>SSO Login</h3>
  <p><a href="/oauth/authorize?client_id=acme-internal&redirect_uri=http://localhost:3000/oauth/callback&response_type=code&scope=profile">Login via AcmeCorp SSO</a></p>
</div></body></html>"""

# ── Auth routes ───────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(INDEX_HTML)

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    email    = data.get("email", "")
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400
    if username in USERS_BY_NAME or username in REGISTERED:
        return jsonify({"error": "Username taken"}), 409
    uid  = 100 + len(REGISTERED)
    user = {"id": uid, "username": username, "password": password,
            "role": "user", "email": email, "dept": "Unknown"}
    REGISTERED[username] = user
    return jsonify({"message": "Registered", "id": uid}), 201

@app.route("/api/auth/login", methods=["POST"])
def login():
    data     = request.get_json() or {}
    username = data.get("username", "")
    password = data.get("password", "")

    user = USERS_BY_NAME.get(username) or REGISTERED.get(username)
    if not user or user["password"] != password:
        return jsonify({"error": "Invalid credentials"}), 401

    payload = {
        "sub":      user["id"],
        "username": user["username"],
        "role":     user["role"],      # VULN 3: role embedded, trusted on decode
        "email":    user["email"],
        "iat":      int(time.time()),
        "exp":      int(time.time()) + 86400,
    }
    token = make_jwt(payload)

    # VULN 6: also set an ECB-encrypted role cookie
    ecb_cookie = ecb_encrypt(f"user={username}|role={user['role']}|dept={user['dept']}")

    resp = make_response(jsonify({
        "token":      token,
        "user":       {k: v for k, v in user.items() if k != "password"},
        "note":       "Set Authorization: Bearer <token> on subsequent requests",
    }))
    resp.set_cookie("session_role", ecb_cookie, httponly=False)  # VULN: httponly=False
    return resp

# ── API routes ────────────────────────────────────────────────

@app.route("/api/profile")
@jwt_required
def profile():
    p = request.jwt_payload
    uid = p.get("sub")
    user = USERS.get(uid) or next(
        (u for u in REGISTERED.values() if u["id"] == uid), None
    )
    return jsonify(user or p)

@app.route("/api/users/<int:uid>")
@jwt_required
def get_user(uid):
    # VULN: IDOR — any authenticated user can look up anyone
    user = USERS.get(uid)
    if not user:
        return jsonify({"error": "Not found"}), 404
    return jsonify({k: v for k, v in user.items() if k != "password"})

@app.route("/api/payroll")
@jwt_required
def payroll():
    p = request.jwt_payload
    data = {
        "employee":   p.get("username"),
        "salary":     "$0 — you're a hacker, not an employee 😄",
        "bonus":      "FLAG{jwt_auth_bypassed}" if p.get("role") == "admin" else None,
        "department": p.get("dept", "Unknown"),
    }
    return jsonify(data)

@app.route("/api/admin/dashboard")
@admin_required
def admin_dashboard():
    return jsonify({
        "message":  "Welcome to the AcmeCorp admin panel",
        "users":    [
            {k: v for k, v in u.items() if k != "password"}
            for u in list(USERS.values()) + list(REGISTERED.values())
        ],
        "hint": "The real flag is at /api/admin/flag",
    })

@app.route("/api/admin/flag")
@admin_required
def admin_flag():
    return jsonify({
        "flag":    "FLAG{crypto_and_jwt_fully_pwned}",
        "message": "Congratulations — you exploited the JWT/OAuth/crypto vulnerabilities!",
        "attacker": request.jwt_payload.get("username", "unknown"),
    })

# VULN 7: Debug endpoint leaks config
@app.route("/api/debug")
def debug():
    return jsonify({
        "app":        "AcmeCorp Portal v2.3",
        "jwt_algo":   "HS256",
        "pubkey_hint":"Check /static/keys/public.pem for the SSO public key",  # red herring hint
        "aes_mode":   "ECB",                 # VULN: leaks cipher mode
        "aes_keylen": len(AES_KEY) * 8,      # VULN: leaks key length
        "env":        "production",
        "users_count": len(USERS) + len(REGISTERED),
    })

# ── Cookie-based admin route (AES-ECB) ───────────────────────

@app.route("/api/secure-panel")
def secure_panel():
    """
    VULN 6: Reads role from AES-ECB encrypted cookie.
    ECB is deterministic — an attacker who can register a crafted username
    can mix-and-match ciphertext blocks to forge role=admin.

    Block layout (16 bytes each):
      Block 0: "user=AAAAAAAAAA" (14 chars of username prefix)
      Block 1: "role=admin|dept"  ← craft your username so this lands on a block boundary
      Block 2: "=Unknown........"
    """
    cookie = request.cookies.get("session_role", "")
    if not cookie:
        return jsonify({"error": "No session_role cookie"}), 401
    try:
        plaintext = ecb_decrypt(cookie)
        parts = dict(p.split("=", 1) for p in plaintext.split("|") if "=" in p)
        role = parts.get("role", "user")
        if role == "admin":
            return jsonify({
                "access":  "granted",
                "flag":    "FLAG{ecb_block_replay_attack}",
                "message": "You forged an admin cookie via AES-ECB block manipulation!",
            })
        return jsonify({"access": "denied", "role": role,
                        "hint": "Only admins can access this panel"})
    except Exception as e:
        return jsonify({"error": "Invalid cookie", "detail": str(e)}), 400

# ── OAuth 2.0 endpoints ───────────────────────────────────────

@app.route("/oauth/authorize")
def oauth_authorize():
    client_id    = request.args.get("client_id", "")
    redirect_uri = request.args.get("redirect_uri", "")
    state        = request.args.get("state", "")   # VULN 5: state not validated
    scope        = request.args.get("scope", "profile")
    username     = request.args.get("username", "")
    password     = request.args.get("password", "")

    client = OAUTH_CLIENTS.get(client_id)
    if not client:
        return jsonify({"error": "Unknown client_id"}), 400

    # VULN 4: only checks prefix, not exact match
    allowed = any(redirect_uri.startswith(uri) for uri in client["redirect_uris"])
    if not allowed:
        # Extra VULN: also allows localhost with any port
        from urllib.parse import urlparse
        parsed = urlparse(redirect_uri)
        allowed = parsed.hostname in ("localhost", "127.0.0.1")

    if not allowed:
        return jsonify({"error": "Invalid redirect_uri"}), 400

    # Show login form if no credentials submitted
    if not username:
        return render_template_string(OAUTH_LOGIN_HTML,
            client_name=client["name"],
            redirect_uri=redirect_uri,
            client_id=client_id,
            state=state,
            scope=scope)

    # Authenticate
    user = USERS_BY_NAME.get(username) or REGISTERED.get(username)
    if not user or user["password"] != password:
        return render_template_string(OAUTH_LOGIN_HTML,
            client_name=client["name"],
            redirect_uri=redirect_uri,
            client_id=client_id,
            state=state,
            scope=scope,
            error="Invalid credentials")

    # Issue auth code
    code = secrets.token_urlsafe(16)
    OAUTH_CODES[code] = {"user_id": user["id"], "expires": time.time() + 600}

    # VULN 4: redirect to attacker-controlled URI if they bypass the prefix check
    sep = "&" if "?" in redirect_uri else "?"
    # VULN 5: state echoed back but never validated server-side
    return redirect(f"{redirect_uri}{sep}code={code}&state={state}")

@app.route("/oauth/token", methods=["POST"])
def oauth_token():
    code          = request.form.get("code", "")
    client_id     = request.form.get("client_id", "")
    client_secret = request.form.get("client_secret", "")
    grant_type    = request.form.get("grant_type", "")

    client = OAUTH_CLIENTS.get(client_id)
    if not client or client["secret"] != client_secret:
        return jsonify({"error": "invalid_client"}), 401

    entry = OAUTH_CODES.pop(code, None)
    if not entry or time.time() > entry["expires"]:
        return jsonify({"error": "invalid_grant"}), 400

    user = USERS.get(entry["user_id"])
    access_token = secrets.token_urlsafe(32)
    OAUTH_TOKENS[access_token] = {"user_id": user["id"], "scope": "profile"}

    # VULN: also issues a JWT with the weak secret
    jwt_token = make_jwt({
        "sub":      user["id"],
        "username": user["username"],
        "role":     user["role"],
        "iat":      int(time.time()),
        "exp":      int(time.time()) + 3600,
    })

    return jsonify({
        "access_token":  access_token,
        "token_type":    "Bearer",
        "expires_in":    3600,
        "jwt":           jwt_token,          # VULN: leaks JWT on token exchange
        "scope":         "profile",
    })

@app.route("/oauth/userinfo")
def oauth_userinfo():
    auth  = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip()
    entry = OAUTH_TOKENS.get(token)
    if not entry:
        return jsonify({"error": "invalid_token"}), 401
    user = USERS.get(entry["user_id"])
    return jsonify({k: v for k, v in user.items() if k != "password"})

OAUTH_LOGIN_HTML = """<!DOCTYPE html>
<html>
<head><title>AcmeCorp SSO</title>
<style>
  body{font-family:sans-serif;background:#2c3e50;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}
  .card{background:#fff;padding:40px;border-radius:8px;box-shadow:0 4px 20px rgba(0,0,0,.3);width:360px}
  h2{margin-top:0;color:#2c3e50}input{width:100%;padding:10px;margin:8px 0;box-sizing:border-box;border:1px solid #ddd;border-radius:4px}
  button{width:100%;padding:12px;background:#2980b9;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:15px}
  .error{color:#e74c3c;margin-bottom:10px}.app-name{color:#7f8c8d;font-size:14px}
</style>
</head>
<body><div class="card">
  <h2>🔐 AcmeCorp SSO</h2>
  <p class="app-name">Sign in to access: <strong>{{ client_name }}</strong></p>
  {% if error %}<div class="error">{{ error }}</div>{% endif %}
  <form method="POST" action="/oauth/authorize">
    <input type="hidden" name="client_id"    value="{{ client_id }}">
    <input type="hidden" name="redirect_uri" value="{{ redirect_uri }}">
    <input type="hidden" name="state"        value="{{ state }}">
    <input type="hidden" name="scope"        value="{{ scope }}">
    <input type="text"     name="username" placeholder="Username" autofocus>
    <input type="password" name="password" placeholder="Password">
    <button type="submit">Sign In</button>
  </form>
</div></body></html>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
