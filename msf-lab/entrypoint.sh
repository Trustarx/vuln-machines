#!/bin/bash
# Start all vulnerable services

echo "=========================================="
echo "  MSF Lab - Metasploit Practice Target"
echo "=========================================="
echo ""
echo "  Exploit vectors:"
echo "    [1] vsftpd 2.3.4 backdoor     port 21  (+ 6200)"
echo "        MSF: exploit/unix/ftp/vsftpd_234_backdoor"
echo ""
echo "    [2] Apache Shellshock CGI     port 80"
echo "        MSF: exploit/multi/http/apache_mod_cgi_bash_env_exec"
echo "        Path: /cgi-bin/test.cgi"
echo ""
echo "    [3] distcc daemon RCE         port 3632"
echo "        MSF: exploit/unix/misc/distcc_exec"
echo ""
echo "=========================================="

# Start distcc as root (intentionally insecure)
distccd --daemon \
    --allow 0.0.0.0/0 \
    --no-detach \
    --log-stderr \
    --user root \
    --port 3632 &

echo "[+] distcc started on :3632"

# Start shellshock HTTP server
python3 /services/shellshock_server.py &
echo "[+] Shellshock HTTP server started on :80"

# Start vsftpd backdoor simulation
python3 /services/ftp_backdoor.py &
echo "[+] vsftpd 2.3.4 backdoor simulation started on :21"

# Keep container alive and tail logs
wait
