#!/bin/bash
# ============================================================
# MSF Lab - Service & Flag Setup
# FOR EDUCATIONAL / PENTESTING PRACTICE ONLY
# ============================================================
set -e

echo "[*] Installing services..."

apt-get update -qq
apt-get install -y -qq \
    python3 \
    distcc \
    netcat-traditional \
    net-tools \
    curl \
    nmap \
    iproute2 \
    2>/dev/null

# ── distcc configuration ────────────────────────────────────
echo "[+] Configuring distcc (CVE: no-auth RCE on port 3632)"
# Allow connections from anywhere, run as root for max impact
mkdir -p /etc/distcc
cat > /etc/distcc/clients.allow << 'EOF'
0.0.0.0/0
EOF

# ── Low-priv user ────────────────────────────────────────────
echo "[+] Creating low-privilege user 'daemon-user'"
useradd -m -s /bin/bash daemon-user 2>/dev/null || true
echo "daemon-user:daemon123" | chpasswd

# ── Flags ────────────────────────────────────────────────────
echo "[+] Planting flags"

mkdir -p /home/daemon-user
echo "FLAG{user_shell_obtained}" > /home/daemon-user/user.txt
chown daemon-user:daemon-user /home/daemon-user/user.txt
chmod 644 /home/daemon-user/user.txt

mkdir -p /root
echo "FLAG{root_shell_msf_rce}" > /root/root.txt
chmod 600 /root/root.txt

# Plant a breadcrumb loot file to reward recon
cat > /home/daemon-user/notes.txt << 'EOF'
Internal service notes (DO NOT SHARE)
--------------------------------------
- FTP service running vsftpd 2.3.4 (legacy, do not upgrade - breaks backup scripts)
- HTTP on port 80 - Apache mod_cgi enabled for legacy reporting tools
- distcc left open on 3632 for dev team build farm access
- Root flag in /root/root.txt
EOF
chown daemon-user:daemon-user /home/daemon-user/notes.txt

echo "[*] Setup complete."
