#!/bin/bash
# wp-lab init — one-shot WordPress install with intentionally weak users.
# Runs in the background of the wp-lab-web container. Idempotent.
set -e

cd /var/www/html

echo "[wp-lab] waiting for apache to write wp-config.php..."
for i in $(seq 1 60); do
    [ -f wp-config.php ] && break
    sleep 2
done

echo "[wp-lab] waiting for database..."
DB_HOST="${WORDPRESS_DB_HOST%%:*}"
for i in $(seq 1 60); do
    if mysqladmin ping -h"$DB_HOST" \
            -u"$WORDPRESS_DB_USER" \
            -p"$WORDPRESS_DB_PASSWORD" --silent 2>/dev/null; then
        break
    fi
    sleep 2
done

if wp core is-installed --allow-root 2>/dev/null; then
    echo "[wp-lab] WordPress already installed, skipping setup"
    exit 0
fi

echo "[wp-lab] installing WordPress..."
wp core install \
    --url="${WP_SITE_URL:-http://localhost:8091}" \
    --title="MidwestRealty Properties" \
    --admin_user="${WP_ADMIN_USER:-admin}" \
    --admin_password="${WP_ADMIN_PASS:-Welcome123!}" \
    --admin_email="admin@midwestrealty.local" \
    --skip-email \
    --allow-root

# Extra users so REST API enumeration is rich
wp user create bob bob@midwestrealty.local \
    --role=author \
    --user_pass="bob123" \
    --display_name="Bob Henderson" \
    --allow-root

wp user create editor editor@midwestrealty.local \
    --role=editor \
    --user_pass="Spring2024!" \
    --display_name="Sarah Mills" \
    --allow-root

# Each user posts at least once so /wp-json/wp/v2/users lists them all
# (the REST endpoint only shows users with published posts by default)
wp post create --post_author=1 --post_title="Welcome to MidwestRealty" \
    --post_content="Premier real estate listings across the Midwest." \
    --post_status=publish --allow-root

wp post create --post_author=2 --post_title="New Listing — 123 Oak Street" \
    --post_content="Beautiful 4-bedroom Craftsman in Pleasant Grove." \
    --post_status=publish --allow-root

wp post create --post_author=3 --post_title="Open House This Weekend" \
    --post_content="Saturday 1-4pm at 456 Maple Avenue." \
    --post_status=publish --allow-root

# Pretty permalinks so /wp-json/wp/v2/users and ?author=N redirects work.
# Write .htaccess ourselves since the wp-cli warning ("special configuration")
# is just because the file doesn't exist yet — write it, set perms, flush rules.
cat > /var/www/html/.htaccess <<'HTACCESS'
# BEGIN WordPress
<IfModule mod_rewrite.c>
RewriteEngine On
RewriteRule .* - [E=HTTP_AUTHORIZATION:%{HTTP:Authorization}]
RewriteBase /
RewriteRule ^index\.php$ - [L]
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule . /index.php [L]
</IfModule>
# END WordPress
HTACCESS
chown www-data:www-data /var/www/html/.htaccess
wp rewrite structure "/%postname%/" --allow-root
wp rewrite flush --hard --allow-root

# Make sure xmlrpc.php is enabled (default, but explicit). System.multicall
# is what makes brute-force amplification interesting.
wp option update default_role subscriber --allow-root

# Drop a hint near the web root so attackers know there's a flag
mkdir -p /var/www/html/wp-content/uploads
cat > /var/www/html/wp-content/uploads/.notes.txt <<'EOF'
internal notes:
  - prod flag is at /flag.txt on the host
  - admin pass change reminder: rotate every 90 days
  - xmlrpc kept enabled because mobile app team still uses it
EOF

# Make sure www-data owns wp-content so plugin upload + media can write
chown -R www-data:www-data /var/www/html/wp-content
find /var/www/html/wp-content -type d -exec chmod 755 {} \;

echo "[wp-lab] setup complete"
