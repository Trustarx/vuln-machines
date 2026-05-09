FROM wordpress:5.8-apache

# Tools needed for the init script + lab realism
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        curl less default-mysql-client unzip ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Enable Apache rewrite + .htaccess overrides so pretty permalinks work
RUN a2enmod rewrite \
 && sed -i 's|AllowOverride None|AllowOverride All|g' /etc/apache2/apache2.conf

# wp-cli for unattended install / user creation
RUN curl -fsSL https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar \
        -o /usr/local/bin/wp \
 && chmod +x /usr/local/bin/wp

COPY init.sh       /usr/local/bin/wp-lab-init.sh
COPY entrypoint.sh /usr/local/bin/wp-lab-entrypoint.sh
RUN chmod +x /usr/local/bin/wp-lab-init.sh /usr/local/bin/wp-lab-entrypoint.sh

# Flag dropped at the OS root so a webshell needs to RCE to read it
COPY flag.txt /flag.txt
RUN chmod 644 /flag.txt

ENTRYPOINT ["/usr/local/bin/wp-lab-entrypoint.sh"]
CMD ["apache2-foreground"]
