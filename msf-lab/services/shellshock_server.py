"""
Shellshock CGI Simulation (CVE-2014-6271)
------------------------------------------
Simulates Apache mod_cgi + bash shellshock vulnerability.
MSF module: exploit/multi/http/apache_mod_cgi_bash_env_exec

Behavior:
  - Serves HTTP on port 80
  - Any request to /cgi-bin/* checks ALL headers for the
    shellshock pattern: () { :;}; <cmd>
  - If found, executes <cmd> as root (reverse shell connects back)
  - Normal paths return a generic Apache-looking page
"""

import http.server
import subprocess
import re
import threading
import sys

SHELLSHOCK_RE = re.compile(r'\(\)\s*\{[^}]*\};\s*(.*)', re.DOTALL)
PORT = 80


class ShellshockHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        self._handle()

    def do_POST(self):
        self._handle()

    def do_HEAD(self):
        self._handle()

    def _handle(self):
        # Check every header for shellshock payload
        triggered = False
        for key, val in self.headers.items():
            match = SHELLSHOCK_RE.search(val)
            if match:
                cmd = match.group(1).strip()
                print(f"[shellshock] Triggered via '{key}' header: {cmd[:80]}", flush=True)
                # Fire and forget — reverse shell connects back to attacker
                threading.Thread(
                    target=lambda c=cmd: subprocess.run(c, shell=True, timeout=30),
                    daemon=True
                ).start()
                triggered = True
                break

        if triggered:
            # Return valid CGI-looking response (MSF checks for this)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"\n")
        elif self.path.startswith("/cgi-bin/"):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Content-Type: text/plain\n\nHello World\n")
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Server", "Apache/2.2.22 (Ubuntu)")
            self.end_headers()
            self.wfile.write(b"""<!DOCTYPE html>
<html><head><title>Apache2 Ubuntu Default Page</title></head>
<body><h1>It works!</h1>
<p>This is the default welcome page for Apache2 on Ubuntu.</p>
</body></html>""")

    def log_message(self, fmt, *args):
        print(f"[shellshock] {self.address_string()} - {fmt % args}", flush=True)


def main():
    server = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), ShellshockHandler)
    print(f"[shellshock] HTTP/CGI service listening on :{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
