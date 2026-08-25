"""WSGI config for the aiyansite project."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aiyansite.settings')

application = get_wsgi_application()
