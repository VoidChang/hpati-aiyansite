"""ASGI config for the aiyansite project."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aiyansite.settings')

application = get_asgi_application()
