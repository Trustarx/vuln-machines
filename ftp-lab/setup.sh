#!/bin/bash
# FTP Lab - Setup Script
# FOR EDUCATIONAL / PENTESTING PRACTICE ONLY
set -e

export DEBIAN_FRONTEND=noninteractive

echo "[*] Installing packages..."
apt-get update -qq
apt-get install -y -qq \
    proftpd-basic \
    apache2 \
    openssh-server \
    sudo \
    cron \
    curl \
    net-tools \
    ncat \
    php \
    libapache2-mod-php 2>/dev/null

# ── Users ────────────────────────────────────────────────────
echo "[+] Creating users"
useradd -m -s /bin/bash ftpuser 2>/dev/null || true
echo "ftpuser:Welc0me2Acme!" | chpasswd
useradd -m -s /bin/bash sysadmin 2>/dev/null || true
echo "sysadmin:S3cur3DB2019!" | chpasswd

# Add ftpuser to www-data group (realistic but exploitable)
usermod -aG www-data ftpuser

# ── FTP directory setup ──────────────────────────────────────
echo "[+] Setting up FTP directories"
mkdir -p /var/ftp/pub
cp -r /ftp-files/pub/. /var/ftp/pub/
chown -R ftp:nogroup /var/ftp
chmod -R 755 /var/ftp

# ── Apache web root ──────────────────────────────────────────
echo "[+] Setting up web server"
mkdir -p /var/www/html
cat > /var/www/html/index.html << 'HTML'
<!DOCTYPE html>
<html>
<head><title>AcmeCorp Internal Portal</title>
<style>body{font-family:Arial,sans-serif;max-width:700px;margin:80px auto;color:#333}
h1{color:#2c3e50}p{color:#666}.footer{margin-top:60px;font-size:12px;color:#aaa}</style>
</head>
<body>
  <h1>AcmeCorp Internal Portal</h1>
  <p>Welcome to the AcmeCorp employee portal.</p>
  <p>For IT support contact: <a href="mailto:it@acmecorp.local">it@acmecorp.local</a></p>
  <div class="footer">AcmeCorp &copy; 2021 | Powered by Apache/2.4</div>
</body>
</html>
HTML

# www-data owns web root — proftpd running as www-data can write here
chown -R www-data:www-data /var/www/html
chmod 755 /var/www/html

# ── ProFTPD config ───────────────────────────────────────────
echo "[+] Configuring ProFTPD"
cp /proftpd.conf /etc/proftpd/proftpd.conf
mkdir -p /var/log/proftpd
touch /var/log/proftpd/proftpd.log /var/log/proftpd/xferlog
chown -R www-data:www-data /var/log/proftpd

# ── SSH setup ────────────────────────────────────────────────
echo "[+] Configuring SSH"
mkdir -p /run/sshd /etc/ssh
ssh-keygen -A 2>/dev/null || true
sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config

# ── Privesc vector: writable cron script ─────────────────────
echo "[+] Setting up privesc vectors"
mkdir -p /opt/maintenance

cat > /opt/maintenance/cleanup.sh << 'CRON'
#!/bin/bash
# Maintenance cleanup - removes old temp files
find /tmp -name "*.tmp" -mtime +1 -delete 2>/dev/null
find /var/log -name "*.gz" -mtime +30 -delete 2>/dev/null
CRON

# VULN: script is world-writable, runs as root every minute
chmod 777 /opt/maintenance/cleanup.sh
echo "* * * * * root /opt/maintenance/cleanup.sh" > /etc/cron.d/maintenance
chmod 644 /etc/cron.d/maintenance

# VULN: sudo misconfiguration - ftpuser can run vim as root
echo "ftpuser ALL=(root) NOPASSWD: /usr/bin/vim" > /etc/sudoers.d/ftpuser
chmod 440 /etc/sudoers.d/ftpuser

# ── PHP for webshell execution ────────────────────────────────
a2enmod php* 2>/dev/null || true

# ── Flags ────────────────────────────────────────────────────
echo "[+] Planting flags"
echo "FLAG{ftp_anon_creds_user_shell}" > /home/ftpuser/user.txt
chmod 644 /home/ftpuser/user.txt
chown ftpuser:ftpuser /home/ftpuser/user.txt

echo "FLAG{proftpd_modcopy_rce_path}" > /home/ftpuser/webshell_note.txt
chmod 644 /home/ftpuser/webshell_note.txt

echo "FLAG{root_via_writable_cron_or_sudo_vim}" > /root/root.txt
chmod 600 /root/root.txt

echo "[*] Setup complete."
