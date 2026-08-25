"""
Create a default superuser on first deploy if none exists yet.

Render's free Postgres is ephemeral-ish on the free tier; this guarantees
there's always an admin login available after migrations run. Set the
password via the ADMIN_INITIAL_PASSWORD env var (Render dashboard). If unset,
falls back to a clearly-temporary value that you should change immediately.

Usage:
    python manage.py init_admin
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create a default superuser if no users exist yet.'

    def handle(self, *args, **options):
        User = get_user_model()
        if User.objects.exists():
            self.stdout.write('Users already exist — skipping admin creation.')
            return

        password = os.environ.get('ADMIN_INITIAL_PASSWORD', '').strip()
        if not password:
            self.stdout.write(self.style.WARNING(
                'ADMIN_INITIAL_PASSWORD not set — skipping admin creation. '
                'Create one manually with `python manage.py createsuperuser`.'
            ))
            return

        username = os.environ.get('ADMIN_USERNAME', 'admin')
        email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(
            f'Created superuser "{username}". Please change the password ASAP.'
        ))
