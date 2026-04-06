#!/bin/bash
# Start services and run the vulnerable app as low-priv user

# Start cron (needed for the writable cron privesc vector)
service cron start

# Start SSH (for pivoting practice)
mkdir -p /run/sshd
/usr/sbin/sshd

echo "=========================================="
echo "  Privesc Lab is running!"
echo "  Web app:  http://localhost:8080"
echo "  SSH:      ssh webuser@localhost -p 2222"
echo "  Password: websecure123"
echo "=========================================="

# Run the web app as the low-privilege user
su - webuser -c "cd /app && python3 app.py"
