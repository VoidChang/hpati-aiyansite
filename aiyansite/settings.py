"""
Django settings for aiyansite project.

The new website for 艾研信息 (AiYan Information) — rebuilt clean and minimal,
inspired by the design language of Apple and Google.
"""
import os
from pathlib import Path

import dj_database_url
import environ

# Build paths inside the project so templates/static resolve reliably.
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment — read from .env locally, from Render's dashboard in production.
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(str, ''),
    SECRET_KEY=(str, ''),
    DATABASE_URL=(str, ''),
    SECURE_SSL_REDIRECT=(bool, True),
)
env_file = BASE_DIR / '.env'
if env_file.exists():
    environ.Env.read_env(str(env_file))

# Fallbacks so a fresh checkout still runs out of the box.
SECRET_KEY = env('SECRET_KEY') or 'django-insecure-dev-key-change-me-in-production-0123456789'
DEBUG = env('DEBUG', default=True)

# Render exposes the app on port 10000 and proxies traffic; allow the host.
allowed = env('ALLOWED_HOSTS', default='')
ALLOWED_HOSTS = [h.strip() for h in allowed.split(',') if h.strip()] or ['*']

# Render terminates TLS upstream — trust the proxy header.
CSRF_TRUSTED_ORIGINS = [o for o in os.environ.get(
    'CSRF_TRUSTED_ORIGINS', 'https://*.onrender.com'
).split(',') if o]

# --------------------------------------------------------------------------- #
# Applications
# --------------------------------------------------------------------------- #
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'website.apps.WebsiteConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'aiyansite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'website.context_processors.site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'aiyansite.wsgi.application'
ASGI_APPLICATION = 'aiyansite.asgi.application'

# --------------------------------------------------------------------------- #
# Database — sqlite for local dev, postgres URL on Render.
# --------------------------------------------------------------------------- #
DATABASE_URL = env('DATABASE_URL', default='sqlite:///db.sqlite3')
DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=False)
}

# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --------------------------------------------------------------------------- #
# Internationalisation
# --------------------------------------------------------------------------- #
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------- #
# Static & media — WhiteNoise serves static in production; media uses
# FileField uploads persisted to disk (Render's persistent disk or ephemeral).
# --------------------------------------------------------------------------- #
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Security hardening (active when DEBUG=False).
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    # Allow disabling SSL redirect when serving on a bare IP (no TLS cert yet).
    SECURE_SSL_REDIRECT = env('SECURE_SSL_REDIRECT', default=True)
    SESSION_COOKIE_SECURE = env('SECURE_SSL_REDIRECT', default=True)
    CSRF_COOKIE_SECURE = env('SECURE_SSL_REDIRECT', default=True)
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'
    X_FRAME_OPTIONS = 'DENY'

# --------------------------------------------------------------------------- #
# First-run helper: create a default superuser password for Render review.
# Set via env in production. Left empty = not used.
# --------------------------------------------------------------------------- #
ADMIN_INITIAL_PASSWORD = os.environ.get('ADMIN_INITIAL_PASSWORD', '')
