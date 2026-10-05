from dataclasses import dataclass
import hmac
from django.conf import settings
from rest_framework import permissions
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


@dataclass(frozen=True)
class SistemaAutorizado:
    sistema: str
    permisos: frozenset


class ExternoApiKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        supplied = request.headers.get('X-Api-Key')
        if not supplied: return None
        keys = {**settings.AGENDA_API_KEYS, **settings.EXPEDIENTES_API_KEYS}
        for secret, config in keys.items():
            if hmac.compare_digest(supplied.encode(), secret.encode()):
                if isinstance(config, str):
                    return (None, SistemaAutorizado(config.strip().upper(), frozenset({'reservar', 'consultar'})))
                return (None, SistemaAutorizado(config['sistema'].strip().upper(), frozenset(config['permisos'])))
        raise AuthenticationFailed('Credencial de servicio invalida.')

    def authenticate_header(self, request): return 'Api-Key'


class EsAplicacionExterna(permissions.BasePermission):
    def has_permission(self, request, view):
        return isinstance(request.auth, SistemaAutorizado) and getattr(view, 'permiso_servicio', 'reservar') in request.auth.permisos
