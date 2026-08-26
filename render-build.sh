#!/usr/bin/env bash
# Render build script — installs deps, collects static, runs migrations.
set -euo pipefail

echo "==> Installing Python dependencies"
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Collecting static files"
python manage.py collectstatic --noinput

echo "==> Applying database migrations"
python manage.py migrate --noinput

echo "==> Seeding content (idempotent)"
python manage.py seed || true

echo "==> Fetching product images from hpati.com"
python manage.py seed_media || true

echo "==> Seeding resource centre metadata"
python manage.py seed_resource || true

echo "==> Creating default admin if needed"
python manage.py init_admin || true

echo "==> Build complete."
