#!/bin/bash
# wp-lab entrypoint — fires the lab init in the background, then hands
# control to the upstream WordPress entrypoint (which writes wp-config.php
# and execs apache2-foreground).
set -e

(/usr/local/bin/wp-lab-init.sh > /var/log/wp-lab-init.log 2>&1) &

exec docker-entrypoint.sh "$@"
