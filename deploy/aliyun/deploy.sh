#!/usr/bin/env bash
# deploy.sh — Zero-downtime release for the AiYan website on Alibaba Cloud
# Linux 4. Strategy: hot reload gunicorn via `systemctl reload` (HUP), which
# lets the master fork new workers while old ones finish in-flight requests.
#
# For large dependency changes use blue-green with --blue-green:
#   1. clone to /data/web_new on port 8001
#   2. smoke test
#   3. flip nginx upstream
#   4. sync code to /data/web, restart, flip back
#
# Usage:
#   sudo bash deploy.sh [--branch main] [--blue-green] [--no-migrate]
set -euo pipefail

INSTALL_DIR=/data/web
BRANCH=main
BLUE_GREEN=0
SKIP_MIGRATE=0
BACKUP_DIR=/data/backup
LOG_FILE=/var/log/aiyan/deploy.log

while [[ $# -gt 0 ]]; do
    case "$1" in
        --branch)       BRANCH="$2"; shift 2 ;;
        --blue-green)  BLUE_GREEN=1; shift ;;
        --no-migrate)  SKIP_MIGRATE=1; shift ;;
        -h|--help)
            sed -n '2,18p' "$0"; exit 0 ;;
        *) echo "[err] unknown arg: $1"; exit 2 ;;
    esac
done

if [[ $EUID -ne 0 ]]; then
    echo "[err] run as root: sudo bash $0 ..."; exit 1
fi

mkdir -p "$BACKUP_DIR" "$(dirname "$LOG_FILE")"
exec > >(tee -a "$LOG_FILE") 2>&1
echo
echo "==================== $(date '+%F %T') deploy start ===================="

cd "$INSTALL_DIR"

# ---------------------------------------------------------------- #
# Pre-flight: backup DB + current code
# ---------------------------------------------------------------- #
echo "==> [1/5] Backup"
TS=$(date +%Y%m%d-%H%M%S)
sudo -u postgres pg_dump aiyan | gzip > "$BACKUP_DIR/db-$TS.sql.gz"
find "$BACKUP_DIR" -name 'db-*.sql.gz' -mtime +7 -delete
tar czf "$BACKUP_DIR/code-$TS.tar.gz" \
    --exclude=venv --exclude=media --exclude=staticfiles --exclude=.git \
    -C "$(dirname "$INSTALL_DIR")" "$(basename "$INSTALL_DIR")" || true

# ---------------------------------------------------------------- #
# Pull new code
# ---------------------------------------------------------------- #
echo "==> [2/5] Pulling origin/$BRANCH"
git fetch origin "$BRANCH"
OLD=$(git rev-parse HEAD)
git reset --hard "origin/$BRANCH"
NEW=$(git rev-parse HEAD)
if [[ "$OLD" == "$NEW" ]]; then
    echo "    already up-to-date at $NEW; nothing to do"; exit 0
fi
echo "    $OLD -> $NEW"

# ---------------------------------------------------------------- #
# Deps (only if requirements.txt changed)
# ---------------------------------------------------------------- #
echo "==> [3/5] Sync deps"
source venv/bin/activate
if ! git diff --quiet "$OLD" "$NEW" -- requirements.txt; then
    pip install -r requirements.txt
else
    echo "    requirements.txt unchanged — skipping pip install"
fi

# ---------------------------------------------------------------- #
# Migrate + collectstatic
# ---------------------------------------------------------------- #
echo "==> [4/5] Migrate / collectstatic"
if [[ $SKIP_MIGRATE -eq 0 ]]; then
    python manage.py migrate --noinput
else
    echo "    --no-migrate given, skipping"
fi
python manage.py collectstatic --noinput

# ---------------------------------------------------------------- #
# Reload
# ---------------------------------------------------------------- #
if [[ $BLUE_GREEN -eq 1 ]]; then
    echo "==> [5/5] Blue-green reload"
    NEW_DIR=$INSTALL_DIR.new
    PORT_NEW=8001
    rsync -a --delete --exclude=venv --exclude=media --exclude=staticfiles \
        --exclude=.git --exclude=.env "$INSTALL_DIR/" "$NEW_DIR/"
    python3 -m venv "$NEW_DIR/venv_new"
    source "$NEW_DIR/venv_new/bin/activate"
    pip install -r "$NEW_DIR/requirements.txt" gunicorn psycopg2-binary
    cp "$INSTALL_DIR/.env" "$NEW_DIR/.env"

    /data/web/venv/bin/gunicorn aiyansite.wsgi:application \
        --bind 127.0.0.1:$PORT_NEW --workers 3 --daemon \
        --pid /tmp/aiyan-new.pid

    echo "    smoke test on :$PORT_NEW"
    for i in {1..10}; do
        code=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT_NEW/" || echo 000)
        [[ "$code" == "200" ]] && break || sleep 2
    done
    [[ "$code" == "200" ]] || { echo "[err] smoke test failed ($code)"; kill "$(cat /tmp/aiyan-new.pid)"; exit 1; }

    # Flip nginx upstream to 8001
    sed -i "s/127\.0\.0\.1:8000/127.0.0.1:$PORT_NEW/" /etc/nginx/conf.d/aiyan.conf
    nginx -t && systemctl reload nginx
    echo "    nginx flipped to :$PORT_NEW"

    # Promote new code to /data/web and restart main instance
    rsync -a --delete --exclude=venv --exclude=media --exclude=staticfiles \
        --exclude=.git --exclude=.env "$NEW_DIR/" "$INSTALL_DIR/"
    rm -rf "$NEW_DIR"
    systemctl restart aiyan

    sleep 3
    sed -i "s/127\.0\.0\.1:$PORT_NEW/127.0.0.1:8000/" /etc/nginx/conf.d/aiyan.conf
    nginx -t && systemctl reload nginx
    kill "$(cat /tmp/aiyan-new.pid)" 2>/dev/null || true
    rm -f /tmp/aiyan-new.pid
    echo "    blue-green complete"
else
    echo "==> [5/5] Hot reload (systemctl reload aiyan)"
    systemctl reload aiyan
    sleep 2
    systemctl is-active aiyan >/dev/null && echo "    gunicorn reloaded OK" || {
        echo "[err] aiyan not active after reload"; systemctl status aiyan --no-pager; exit 1
    }
fi

# Smoke test the live site
echo "==> Live check"
code=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/ || echo 000)
if [[ "$code" == "200" ]]; then
    echo "    http://127.0.0.1:8000/ -> 200 ✓"
else
    echo "[warn] http://127.0.0.1:8000/ -> $code"
fi

echo "==================== $(date '+%F %T') deploy done  ===================="
