"""Solo para trasladar instalaciones previas de auth.User a usuarios.User.

Ejecutar migrate con estos settings antes de usar los settings normales.
Evita cambiar la dependencia del admin antes de crear usuarios.0001_initial.
"""
from .settings import *  # noqa: F403

AUTH_USER_MODEL = 'auth.User'
