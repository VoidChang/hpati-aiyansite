#!/usr/bin/env bash
# setup.sh — One-shot installer for Alibaba Cloud Linux 4 LTS.
# Installs deps, PostgreSQL, Nginx, systemd unit, and brings the app online.
#
# Usage:
#   sudo bash setup.sh \
#       --domain aiyan.example.com \
#       --repo https://github.com/VoidChang/hpati-aiyansite.git \
#       [--branch main] \
#       [--db-pass <password>] \
#       [--admin-pass <password>] \
#       [--install-dir /data/web]
set -euo pipefail

# ---------------------------------------------------------------- #
# Defaults & arg parsing
# ---------------------------------------------------------------- #
DOMAIN=""
REPO="https://github.com/VoidChang/hpati-aiyansite.git"
BRANCH="main"
DB_PASS=""
ADMIN_PASS=""
INSTALL_DIR="/data/web"
LOG_DIR="/var/log/aiyan"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --domain)        DOMAIN="$2"; shift 2 ;;
        --repo)          REPO="$2"; shift 2 ;;
        --branch)        BRANCH="$2"; shift 2 ;;
        --db-pass)       DB_PASS="$2"; shift 2 ;;
        --admin-pass)    ADMIN_PASS="$2"; shift 2 ;;
        --install-dir)   INSTALL_DIR="$2"; shift 2 ;;
        -h|--help)
            sed -n '2,15p' "$0"; exit 0 ;;
        *)
            echo "[err] unknown arg: $1"; exit 2 ;;
    esac
done

if [[ $EUID -ne 0 ]]; then
    echo "[err] run as root: sudo bash $0 ..."; exit 1
fi
if [[ -z "$DOMAIN" ]]; then
    echo "[err] --domain is required"; exit 2
fi
if [[ -z "$DB_PASS" ]]; then
    DB_PASS="$(head -c 24 /dev/urandom | base64 | tr -d '/+=' | cut -c1-24)"
    echo "[info] generated DB_PASS (save it!): $DB_PASS"
fi
if [[ -z "$ADMIN_PASS" ]]; then
    ADMIN_PASS="$(head -c 16 /dev/urandom | base64 | tr -d '/+=' | cut -c1-16)"
    echo "[info] generated ADMIN_PASS (save it!): $ADMIN_PASS"
fi

echo "==> Config"
echo "    domain   : $DOMAIN"
echo "    repo     : $REPO ($BRANCH)"
echo "    install  : $INSTALL_DIR"
echo

# ---------------------------------------------------------------- #
# 1. System packages
# ---------------------------------------------------------------- #
echo "==> Installing system packages"
dnf install -y epel-release
dnf groupinstall -y "Development Tools"
dnf install -y \
    python3 python3-devel python3-pip \
    nginx \
    postgresql-server postgresql-devel \
    git tar wget curl \
    policycoreutils-python-utils \
    libffi-devel openssl-devel bzip2-devel xz-devel \
    firewalld

# ---------------------------------------------------------------- #
# 2. PostgreSQL
# ---------------------------------------------------------------- #
echo "==> Initialising PostgreSQL"
if [[ ! -f /var/lib/pgsql/data/PG_VERSION ]]; then
    postgresql-setup --initdb
fi

# Switch local auth to scram-sha-256
PG_HBA=/var/lib/pgsql/data/pg_hba.conf
sed -i 's/^\(host\s\+all\s\+all\s\+127\.0\.0\.1\/32\s\+\).*$/\1scram-sha-256/' "$PG_HBA"
sed -i 's/^\(host\s\+all\s\+all\s\+::1\/128\s\+\).*$/\1scram-sha-256/' "$PG_HBA"

systemctl enable --now postgresql

echo "==> Creating database aiyan and user"
sudo -u postgres psql <<EOF
DO \$\$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'aiyan') THEN
        CREATE USER aiyan WITH PASSWORD '$DB_PASS';
    ELSE
        ALTER USER aiyan WITH PASSWORD '$DB_PASS';
    END IF;
END \$\$;
SELECT 'CREATE DATABASE aiyan OWNER aiyan'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'aiyan')\gexec
EOF

# ---------------------------------------------------------------- #
# 3. Code + virtualenv
# ---------------------------------------------------------------- #
echo "==> Cloning repo to $INSTALL_DIR"
mkdir -p "$(dirname "$INSTALL_DIR")"
if [[ ! -d "$INSTALL_DIR/.git" ]]; then
    git clone -b "$BRANCH" "$REPO" "$INSTALL_DIR"
else
    git -C "$INSTALL_DIR" fetch origin "$BRANCH"
    git -C "$INSTALL_DIR" reset --hard "origin/$BRANCH"
fi

echo "==> Creating venv and installing deps"
python3 -m venv "$INSTALL_DIR/venv"
source "$INSTALL_DIR/venv/bin/activate"
pip install --upgrade pip
pip install -r "$INSTALL_DIR/requirements.txt"
pip install gunicorn psycopg2-binary

# ---------------------------------------------------------------- #
# 4. .env
# ---------------------------------------------------------------- #
echo "==> Writing .env"
SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
ALLOWED_HOSTS="$DOMAIN,www.$DOMAIN"

cat > "$INSTALL_DIR/.env" <<EOF
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=$ALLOWED_HOSTS
DATABASE_URL=postgres://aiyan:$DB_PASS@127.0.0.1:5432/aiyan
CSRF_TRUSTED_ORIGINS=https://$DOMAIN,https://www.$DOMAIN
ADMIN_INITIAL_PASSWORD=$ADMIN_PASS
EOF
chmod 600 "$INSTALL_DIR/.env"

# ---------------------------------------------------------------- #
# 5. Django init: migrate / collectstatic / seed / init_admin
# ---------------------------------------------------------------- #
echo "==> Running migrations & collectstatic"
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py seed || true
python manage.py init_admin || true

# ---------------------------------------------------------------- #
# 6. Logs dir + ownership
# ---------------------------------------------------------------- #
mkdir -p "$LOG_DIR"
chown -R nginx:nginx "$LOG_DIR" "$INSTALL_DIR"

# ---------------------------------------------------------------- #
# 7. systemd unit
# ---------------------------------------------------------------- #
echo "==> Installing systemd unit"
cp "$INSTALL_DIR/deploy/aliyun/aiyan.service" /etc/systemd/system/aiyan.service
systemctl daemon-reload
systemctl enable aiyan
systemctl restart aiyan
systemctl --no-pager --full status aiyan || true

# ---------------------------------------------------------------- #
# 8. Nginx site
# ---------------------------------------------------------------- #
echo "==> Installing Nginx config"
SITE_CONF=/etc/nginx/conf.d/aiyan.conf
sed "s|__DOMAIN__|$DOMAIN|g" "$INSTALL_DIR/deploy/aliyun/nginx.conf" > "$SITE_CONF"
nginx -t
systemctl enable nginx
systemctl reload nginx || systemctl restart nginx

# ---------------------------------------------------------------- #
# 9. SELinux + firewalld
# ---------------------------------------------------------------- #
echo "==> SELinux contexts"
semanage fcontext -a -t httpd_sys_content_t "$INSTALL_DIR/staticfiles(/.*)?" 2>/dev/null || true
semanage fcontext -a -t httpd_sys_content_t "$INSTALL_DIR/media(/.*)?" 2>/dev/null || true
restorecon -Rv "$INSTALL_DIR" >/dev/null
setsebool -P httpd_can_network_connect 1

echo "==> Firewalld rules"
systemctl enable --now firewalld
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload

# ---------------------------------------------------------------- #
# 10. Done — next steps
# ---------------------------------------------------------------- #
cat <<EOF

============================================================
✓ Deployment complete on $DOMAIN

Next steps:
  1. DNS — point $DOMAIN and www.$DOMAIN to this ECS EIP
  2. HTTPS — run:
       dnf install -y certbot python3-certbot-nginx
       certbot --nginx -d $DOMAIN -d www.$DOMAIN \\
           --non-interactive --agree-tos -m you@example.com --redirect
  3. Admin login — http://$DOMAIN/admin/
       user: admin   pass: $ADMIN_PASS
  4. Backup DB — crontab:
       0 3 * * * sudo -u postgres pg_dump aiyan | gzip > /data/backup/db-\$(date +\%F).sql.gz

Secrets (keep safe):
  DB_PASS     : $DB_PASS
  ADMIN_PASS : $ADMIN_PASS
  .env file  : $INSTALL_DIR/.env  (chmod 600)
============================================================
EOF
