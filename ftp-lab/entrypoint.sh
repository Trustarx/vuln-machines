#!/bin/bash

echo "=============================================="
echo "  FTP Lab - ProFTPD + Apache + SSH"
echo "=============================================="
echo ""
echo "  Services:"
echo "    FTP:  port 21  (ProFTPD — anon + mod_copy)"
echo "    HTTP: port 80  (Apache  — web root /var/www/html)"
echo "    SSH:  port 22  (OpenSSH)"
echo ""
echo "  Hints:"
echo "    - Try anonymous FTP first"
echo "    - Web root is /var/www/html"
echo "    - mod_copy: SITE CPFR / SITE CPTO"
echo ""
echo "  MSF module: exploit/unix/ftp/proftpd_modcopy_exec"
echo "=============================================="

# Start cron
service cron start 2>/dev/null || /usr/sbin/cron 2>/dev/null || true

# Start SSH
/usr/sbin/sshd

# Start Apache
mkdir -p /run/apache2
apache2ctl start 2>/dev/null || apache2 -D FOREGROUND &
sleep 1

# Start ProFTPD in foreground
echo "[+] Starting ProFTPD..."
/usr/sbin/proftpd --nodaemon --config /etc/proftpd/proftpd.conf
