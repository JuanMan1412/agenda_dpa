from django.conf import settings
from rest_framework import permissions
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class ExternoApiKeyAuthentication(BaseAuthentication):
    """
    La aplicación externa NO inicia sesión como un usuario: manda
    su clave de servicio en el header 'X-Api-Key'. Definan las
    claves válidas en settings.py, por ejemplo:

        AGENDA_API_KEYS = {
            "clave-super-secreta-1": "sistema_expedientes",
        }
    """

    def authenticate(self, request):
        api_key = request.headers.get("X-Api-Key")
        if not api_key:
            return None

        claves = getattr(settings, "AGENDA_API_KEYS", {})
        if api_key not in claves:
            raise AuthenticationFailed("API Key inválida")

        # request.auth queda con el nombre del sistema autenticado
        return (None, claves[api_key])


class EsAplicacionExterna(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.auth is not None
