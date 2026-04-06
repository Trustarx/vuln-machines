"""
Intentionally Vulnerable Web Application
-----------------------------------------
FOR EDUCATIONAL / PENTESTING PRACTICE ONLY.
DO NOT deploy on any network accessible to untrusted users.

Vulnerabilities present:
  - OS command injection via the /ping endpoint
  - Information disclosure via /debug
"""

from flask import Flask, request, render_template_string
import subprocess

app = Flask(__name__)

INDEX_HTML = """
<!DOCTYPE html>
<html>
<head><title>NetCheck - Network Diagnostics</title>
<style>
  body { font-family: monospace; background: #1a1a2e; color: #eee; padding: 40px; }
  h1 { color: #0f3460; }
  input, button { padding: 8px 12px; font-size: 14px; font-family: monospace; }
  input { background: #16213e; color: #eee; border: 1px solid #0f3460; width: 300px; }
  button { background: #e94560; color: white; border: none; cursor: pointer; }
  pre { background: #16213e; padding: 15px; border-radius: 4px; overflow-x: auto; }
  a { color: #e94560; }
</style>
</head>
<body>
  <h1>NetCheck v1.3 - Network Diagnostics</h1>
  <p>Enter a host to check connectivity:</p>
  <form method="POST" action="/ping">
    <input type="text" name="host" placeholder="e.g. 8.8.8.8" />
    <button type="submit">Check</button>
  </form>
  {% if output %}
  <h3>Result:</h3>
  <pre>{{ output }}</pre>
  {% endif %}
  <br/>
  <p><a href="/debug">System Debug Info</a></p>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(INDEX_HTML)


@app.route("/ping", methods=["POST"])
def ping():
    host = request.form.get("host", "")
    # VULNERABLE: unsanitized user input passed directly to shell
    result = subprocess.run(
        f"ping -c 2 {host}",
        shell=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    output = result.stdout + result.stderr
    return render_template_string(INDEX_HTML, output=output)


@app.route("/debug")
def debug():
    # VULNERABLE: information disclosure
    import os
    info = subprocess.run("id; uname -a; cat /etc/os-release", shell=True, capture_output=True, text=True)
    env_vars = {k: v for k, v in os.environ.items()}
    return render_template_string("""
    <pre>System Info:\n{{ sysinfo }}\n\nEnvironment:\n{% for k, v in env.items() %}{{ k }}={{ v }}\n{% endfor %}</pre>
    <a href="/">Back</a>
    """, sysinfo=info.stdout, env=env_vars)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
