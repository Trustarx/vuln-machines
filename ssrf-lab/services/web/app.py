"""
PaperPress — Document Rendering Platform
========================================
Public-facing service. Lets users submit a URL; the backend "renders" it
(actually just fetches the body and returns it as a preview).

VULN 1: SSRF via /api/render
   The URL is filtered with a string-based blacklist. Bypasses include:
     - alternative loopback notations (0.0.0.0, [::], 0177.0.0.1)
     - decimal/octal/hex IP encodings
     - using docker DNS hostnames (metadata, admin) directly
     - capitalised schemes (HTTP://) sneak past lowercase-only checks

VULN 2: The /api/render endpoint follows redirects unconditionally.
   So http://attacker/redirect.php -> http://metadata/... also works
   (DNS-rebinding-style; here just plain HTTP redirect chain).

NOTE: This app is NOT meant to be used in production. It is intentionally
broken so you can practice SSRF detection and exploitation.
"""

from flask import Flask, request, jsonify, render_template_string, abort
import requests
import re

app = Flask(__name__)

# ---------------------------------------------------------------
# Naive URL filter — blocks the obvious things and feels secure.
# ---------------------------------------------------------------
BLACKLIST = [
    "127.0.0.1",
    "localhost",
    "169.254.169.254",      # ← classic AWS metadata
    "metadata.google",      # GCP
    "::1",
    "169.254",              # link-local
]


def url_is_blocked(url: str) -> bool:
    """Return True if the URL contains any blacklisted host substring.

    VULN: this is a substring check on the raw URL string. It misses:
      * alternate IP encodings (decimal, hex, octal)
      * hostname aliases on the docker network (metadata, admin)
      * uppercase scheme bypass (the check is lowercase)
      * IPv6 short-form `[::]`
      * 0.0.0.0 (treated as localhost on many stacks)
    """
    lowered = url.lower()
    for bad in BLACKLIST:
        if bad in lowered:
            return True
    return False


HOMEPAGE = """
<!doctype html>
<html><head>
  <title>PaperPress — Document Rendering</title>
  <link rel="stylesheet"
        href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
</head>
<body class="bg-light">
<div class="container py-5">
  <h1 class="display-5">📄 PaperPress</h1>
  <p class="lead">Internal document rendering &amp; preview platform.</p>

  <div class="card mt-4">
    <div class="card-body">
      <h5>Render a URL</h5>
      <p class="text-muted small">
        Submit any HTTP(S) URL — PaperPress will fetch and preview it for you.
      </p>
      <form method="GET" action="/api/render">
        <div class="input-group">
          <input class="form-control" name="url"
                 placeholder="https://example.com/document.html"
                 value="https://example.com/" />
          <button class="btn btn-primary">Render</button>
        </div>
      </form>
    </div>
  </div>

  <div class="card mt-3">
    <div class="card-body">
      <h6>About</h6>
      <p class="small text-muted mb-1">
        PaperPress v0.4 — running on AWS EC2 (us-east-1).
      </p>
      <p class="small text-muted mb-0">
        Internal admin tools are available at
        <code>http://admin.internal/</code>
        (intranet only — staff with VPN access).
      </p>
    </div>
  </div>
</div>
</body></html>
"""


@app.route("/")
def index():
    return HOMEPAGE


@app.route("/api/render")
def render():
    url = request.args.get("url", "").strip()
    if not url:
        return jsonify(error="missing url"), 400

    if url_is_blocked(url):
        return jsonify(error="URL blocked by security policy",
                       hint="Internal addresses are not permitted"), 403

    try:
        # VULN: follows redirects, no IP re-validation after DNS, long timeout
        r = requests.get(url, timeout=8, allow_redirects=True,
                         headers={"User-Agent": "PaperPress/0.4"})
        body = r.text
        # Truncate huge responses
        if len(body) > 50000:
            body = body[:50000] + "\n...[truncated]..."
        return f"""<!doctype html>
<html><head><title>Preview — {url}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
</head><body class="bg-light"><div class="container py-4">
<a href="/" class="btn btn-sm btn-outline-secondary mb-3">&larr; Home</a>
<h5>Preview of <code>{url}</code></h5>
<p class="text-muted small">HTTP {r.status_code} · Content-Type {r.headers.get('content-type','?')}</p>
<pre class="bg-white border p-3" style="max-height:60vh;overflow:auto;font-size:12px;">{_escape(body)}</pre>
</div></body></html>
""", r.status_code
    except requests.exceptions.RequestException as e:
        return jsonify(error="fetch failed", detail=str(e)[:200]), 502


def _escape(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;"))


@app.route("/health")
def health():
    return "ok\n"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
