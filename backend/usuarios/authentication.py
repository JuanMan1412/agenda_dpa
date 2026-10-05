from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication



def normalize_systems(value):
    if isinstance(value, str):
        value = value.split(',')
    if not isinstance(value, (list, tuple)):
        return set()
    return {item.strip().lower() for item in value if isinstance(item, str) and item.strip()}


def validate_local_claims(token):
    if token.get('local_system') != settings.PORTAL_SYSTEM_CODE:
        raise AuthenticationFailed('Se requiere un token local de Agenda DPA.')
    if settings.PORTAL_SYSTEM_CODE not in normalize_systems(token.get('sistemas')):
        raise AuthenticationFailed('El token no tiene acceso a este sistema.')


class LocalJWTAuthentication(JWTAuthentication):
    """Solo tokens locales; estado y permisos leidos desde la base en cada request."""

    def get_validated_token(self, raw_token):
        token = super().get_validated_token(raw_token)
        validate_local_claims(token)
        return token

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if not user.portal_user_id or user.portal_user_id != validated_token.get('portal_user_id'):
            raise AuthenticationFailed('La identidad local ya no coincide con la sesion.')
        return user
