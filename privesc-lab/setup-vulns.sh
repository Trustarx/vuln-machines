#!/bin/bash
# ============================================================
# Intentional Privilege Escalation Vectors
# FOR EDUCATIONAL / PENTESTING PRACTICE ONLY
# ============================================================

set -e

echo "[*] Setting up privilege escalation vectors..."

# --- Vector 1: SUID binary (find) ---
# 'find' with SUID bit lets you exec commands as root
echo "[+] Vector 1: SUID on /usr/bin/find"
chmod u+s /usr/bin/find

# --- Vector 2: Writable cron job running as root ---
echo "[+] Vector 2: World-writable cron script"
mkdir -p /opt/scripts
cat > /opt/scripts/backup.sh << 'CRONSCRIPT'
#!/bin/bash
# Automated backup - runs every minute as root
tar czf /tmp/backup.tar.gz /var/log 2>/dev/null
CRONSCRIPT
chmod 777 /opt/scripts/backup.sh
echo "* * * * * root /opt/scripts/backup.sh" > /etc/cron.d/backup-job
chmod 644 /etc/cron.d/backup-job

# --- Vector 3: Sudo misconfiguration ---
# The 'webuser' can run vim as root without a password
echo "[+] Vector 3: Sudo misconfiguration (vim as root)"
echo "webuser ALL=(root) NOPASSWD: /usr/bin/vim" > /etc/sudoers.d/webuser
chmod 440 /etc/sudoers.d/webuser

# --- Vector 4: Writable /etc/passwd ---
echo "[+] Vector 4: World-writable /etc/passwd"
chmod 666 /etc/passwd

# --- Vector 5: Readable SSH private key ---
echo "[+] Vector 5: Root SSH key left readable"
mkdir -p /root/.ssh
ssh-keygen -t ed25519 -f /root/.ssh/id_ed25519 -N "" -q
chmod 644 /root/.ssh/id_ed25519
# Copy public key to authorized_keys so it can be used
cp /root/.ssh/id_ed25519.pub /root/.ssh/authorized_keys

# --- Vector 6: Capabilities on python3 ---
echo "[+] Vector 6: CAP_SETUID on python3"
if command -v python3 &>/dev/null; then
    setcap cap_setuid+ep "$(readlink -f $(which python3))" 2>/dev/null || true
fi

# --- Create low-priv user for the web app ---
echo "[+] Creating low-privilege user 'webuser'"
useradd -m -s /bin/bash webuser 2>/dev/null || true
echo "webuser:websecure123" | chpasswd

# Plant a flag in /root
echo "[+] Planting flags"
echo "FLAG{you_got_root_congrats}" > /root/flag.txt
chmod 600 /root/flag.txt
echo "FLAG{initial_foothold}" > /home/webuser/user_flag.txt
chown webuser:webuser /home/webuser/user_flag.txt

echo "[*] Vulnerable environment ready. Happy hacking!"
