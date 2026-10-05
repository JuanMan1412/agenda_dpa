from .settings import *  # noqa: F403

# Base aislada: los tests no leen ni modifican agenda_db.
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
PORTAL_SIGNING_KEY = 'test-only-signing-key-with-at-least-32-bytes'
SIMPLE_JWT = {**SIMPLE_JWT, 'SIGNING_KEY': PORTAL_SIGNING_KEY}  # noqa: F405
