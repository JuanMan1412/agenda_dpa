from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.backends import TokenBackend
from rest_framework_simplejwt.exceptions import TokenBackendError, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from usuarios.authentication import LocalJWTAuthentication, normalize_systems, validate_local_claims
from roles.models import Rol
from roles.permissions import get_user_permissions

User = get_user_model()


class PortalAccessSerializer(serializers.Serializer):
    token = serializers.CharField(trim_whitespace=True, max_length=16384)

    def validate_token(self, value):
        if not isinstance(self.initial_data.get('token'), str):
            raise serializers.ValidationError('El token debe ser un string.')
        return value


def local_auth_response(user):
    role = user.rol.descripcion if user.rol and user.rol.estado else ''
    refresh = RefreshToken.for_user(user)
    refresh['username'] = user.username
    refresh['rol'] = role
    refresh['sistemas'] = [settings.PORTAL_SYSTEM_CODE]
    refresh['local_system'] = settings.PORTAL_SYSTEM_CODE
    refresh['portal_user_id'] = user.portal_user_id
    return {
        'access': str(refresh.access_token), 'refresh': str(refresh),
        'rol': role, 'has_changed_password': user.has_changed_password,
        'user': {
            'id': user.pk, 'username': user.username,
            'nombre': user.nombre, 'apellido': user.apellido,
            'nombre_completo': user.nombre_completo,
            'documento': user.documento, 'portal_user_id': user.portal_user_id,
            'is_active': user.is_active, 'rol': user.rol_id, 'rol_detalle': role,
        },
    }


class PortalAccessView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PortalAccessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            payload = TokenBackend(algorithm='HS256', signing_key=settings.PORTAL_SIGNING_KEY).decode(
                serializer.validated_data['token'], verify=True,
            )
        except TokenBackendError as exc:
            raise AuthenticationFailed('El token del portal es invalido o esta vencido.') from exc
        if payload.get('token_type') != 'access' or not isinstance(payload.get('exp'), (int, float)):
            raise AuthenticationFailed('Se requiere un access token con vencimiento del portal.')
        if settings.PORTAL_SYSTEM_CODE not in normalize_systems(payload.get('sistemas')):
            raise PermissionDenied('El token no tiene acceso a este sistema.')
        identity = payload.get('user_id')
        username = payload.get('username')
        if isinstance(identity, bool) or not isinstance(identity, (int, str)) or not str(identity).strip():
            raise serializers.ValidationError({'detail': 'El token no contiene un ID central valido.'})
        portal_id = str(identity).strip()
        if not isinstance(username, str) or not username.strip():
            raise serializers.ValidationError({'detail': 'El token no contiene un username valido.'})
        username = username.strip()
        if len(portal_id) > 255 or len(username) > User._meta.get_field('username').max_length:
            raise serializers.ValidationError({'detail': 'La identidad excede el largo permitido.'})
        full_name = payload.get('nombre_completo')
        if full_name is not None and (not isinstance(full_name, str) or len(full_name) > 300):
            raise serializers.ValidationError({'detail': 'El nombre del portal no es valido.'})
        try:
            with transaction.atomic():
                user = User.objects.select_for_update().filter(portal_user_id=portal_id).first()
                username_owner = User.objects.select_for_update().filter(username=username).first()
                if user and username_owner and user.pk != username_owner.pk:
                    raise PermissionDenied('El nombre de usuario ya pertenece a otra cuenta local.')
                if user is None and username_owner:
                    user = username_owner
                    if user.portal_user_id and user.portal_user_id != portal_id:
                        raise PermissionDenied('La cuenta local esta vinculada a otra identidad del portal.')
                    if not user.portal_user_id and (user.is_staff or user.is_superuser):
                        raise PermissionDenied('Esta cuenta requiere vinculacion manual con el portal.')
                if user is None:
                    # Alta inicial habilitada; el flag solo gobierna reactivaciones posteriores.
                    user = User(username=username, is_active=True)
                    user.set_unusable_password()
                if not user.is_active:
                    if not settings.PORTAL_AUTO_ENABLE_USERS:
                        raise PermissionDenied('El usuario local se encuentra inactivo.')
                    user.is_active = True
                if user.rol_id is None:
                    user.rol = Rol.objects.filter(descripcion=settings.PORTAL_DEFAULT_ROLE, estado=True).first()
                    if user.rol is None:
                        raise PermissionDenied('El rol local predeterminado no esta habilitado.')
                user.username = username
                user.portal_user_id = portal_id
                if full_name is not None:
                    user.nombre_completo = full_name.strip()
                    parts = full_name.split()
                    user.nombre = (' '.join(parts[:-1]) if len(parts) > 1 else full_name.strip())[:150]
                    user.apellido = (parts[-1] if len(parts) > 1 else '')[:150]
                user.save()
                response = local_auth_response(user)
        except IntegrityError as exc:
            raise PermissionDenied('La identidad coincide con otra cuenta; intenta nuevamente o consulta al administrador.') from exc
        return Response(response)

    def get_authenticate_header(self, request):
        return 'Bearer'


class MyPermissionsView(APIView):
    def get(self, request):
        role, sections = get_user_permissions(request.user)
        return Response({'rol': role, 'secciones': sections})


class LocalTokenRefreshView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = serializers.Serializer(data=request.data)
        serializer.fields['refresh'] = serializers.CharField(max_length=16384)
        serializer.is_valid(raise_exception=True)
        try:
            refresh = RefreshToken(serializer.validated_data['refresh'])
            validate_local_claims(refresh)
            user = LocalJWTAuthentication().get_user(refresh)
        except TokenError as exc:
            raise AuthenticationFailed('El refresh local es invalido o esta vencido.') from exc
        return Response(local_auth_response(user))

    def get_authenticate_header(self, request):
        return 'Bearer'
