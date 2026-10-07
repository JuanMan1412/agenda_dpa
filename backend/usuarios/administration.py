from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.db.models.deletion import Collector, ProtectedError, RestrictedError
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, status
from rest_framework.response import Response

from agenda.views import RegistroPagination
from roles.models import Rol
from roles.permissions import CanManageUsers
from .models import AuditoriaUsuario

User = get_user_model()
ROLES = ('ADMINISTRADOR', 'ADMINISTRATIVO', 'CONSULTOR')


class AdministrativeUserSerializer(serializers.ModelSerializer):
    rol = serializers.SlugRelatedField(slug_field='descripcion', queryset=Rol.objects.filter(estado=True, descripcion__in=ROLES))
    nombre_visible = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'nombre', 'apellido', 'nombre_completo', 'email', 'rol', 'is_active', 'portal_user_id', 'nombre_visible']
        read_only_fields = ['id', 'portal_user_id', 'nombre_visible']

    def get_nombre_visible(self, user):
        return user.nombre_completo or ' '.join(filter(None, [user.nombre, user.apellido])) or user.username

    def validate(self, attrs):
        unknown = set(self.initial_data) - set(self.fields)
        if unknown or 'portal_user_id' in self.initial_data:
            raise serializers.ValidationError('Sólo se pueden modificar los campos locales permitidos.')
        if self.instance:
            for field in ('username', 'nombre', 'apellido', 'nombre_completo'):
                if field in attrs and attrs[field] != getattr(self.instance, field):
                    raise serializers.ValidationError({field: 'La identidad se administra en Portal DPA.'})
        return attrs

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_unusable_password()
        user.save()
        return user


def audit(actor, user, action, data=None):
    AuditoriaUsuario.objects.create(actor=actor, usuario=user, usuario_id_historico=user.pk,
        username_historico=user.username, accion=action, datos=data or {})


def lock_administration():
    # Todas las mutaciones usan la misma fila: serializa incluso altas y borrados.
    get_object_or_404(Rol.objects.select_for_update(), descripcion='ADMINISTRADOR')


def protect_last_admin(user, values=None, deleting=False):
    values = values or {}
    is_admin = user.is_active and user.rol and user.rol.estado and user.rol.descripcion == 'ADMINISTRADOR'
    new_role = values.get('rol', user.rol)
    remains_admin = not deleting and values.get('is_active', user.is_active) and new_role and new_role.estado and new_role.descripcion == 'ADMINISTRADOR'
    if is_admin and not remains_admin and not User.objects.filter(is_active=True, rol__estado=True,
            rol__descripcion='ADMINISTRADOR').exclude(pk=user.pk).exists():
        raise serializers.ValidationError('Debe existir al menos un administrador activo en el sistema.')


def ensure_deletable(user):
    protect_last_admin(user, deleting=True)
    message = 'No se puede eliminar definitivamente este usuario porque posee actividad registrada. Puede desactivarlo para impedir su acceso.'
    for relation in User._meta.related_objects:
        if relation.many_to_many:
            continue
        if relation.related_model is AuditoriaUsuario and relation.field.name == 'usuario':
            continue
        if relation.related_model._base_manager.filter(**{relation.field.name: user}).exists():
            raise serializers.ValidationError(message)
    collector = Collector(using=user._state.db)
    try:
        collector.collect([user])
    except (ProtectedError, RestrictedError):
        raise serializers.ValidationError(message)


def audit_changes(actor, user, before):
    after = {'rol': user.rol.descripcion if user.rol else None, 'is_active': user.is_active, 'email': user.email}
    if before != after:
        audit(actor, user, 'USUARIO_EDITADO', {'anterior': before, 'nuevo': after})
    if before['rol'] != after['rol']:
        audit(actor, user, 'ROL_CAMBIADO', {'rol_anterior': before['rol'], 'rol_nuevo': after['rol']})
    if before['is_active'] != after['is_active']:
        audit(actor, user, 'USUARIO_ACTIVADO' if user.is_active else 'USUARIO_DESACTIVADO')


class UserListView(generics.ListCreateAPIView):
    permission_classes = [CanManageUsers]
    serializer_class = AdministrativeUserSerializer
    pagination_class = RegistroPagination

    def get_queryset(self):
        qs = User.objects.select_related('rol').order_by('username', 'pk')
        query = self.request.query_params.get('q', '').strip()
        if query:
            qs = qs.filter(Q(username__icontains=query) | Q(nombre__icontains=query) | Q(apellido__icontains=query) | Q(nombre_completo__icontains=query))
        role = self.request.query_params.get('rol')
        if role:
            if role not in ROLES:
                raise serializers.ValidationError({'rol': 'Rol inválido.'})
            qs = qs.filter(rol__descripcion=role)
        active = self.request.query_params.get('is_active')
        if active is not None:
            if active not in ('true', 'false'):
                raise serializers.ValidationError({'is_active': 'Estado inválido.'})
            qs = qs.filter(is_active=active == 'true')
        return qs

    @transaction.atomic
    def perform_create(self, serializer):
        lock_administration()
        self.request.user.refresh_from_db()
        self.check_permissions(self.request)
        user = serializer.save()
        audit(self.request.user, user, 'USUARIO_CREADO', {'rol': user.rol.descripcion, 'is_active': user.is_active})


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanManageUsers]
    serializer_class = AdministrativeUserSerializer
    queryset = User.objects.select_related('rol')

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        lock_administration()
        request.user.refresh_from_db()
        self.check_permissions(request)
        user = get_object_or_404(User.objects.select_for_update(), pk=kwargs['pk'])
        serializer = self.get_serializer(user, data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)
        protect_last_admin(user, serializer.validated_data)
        before = {'rol': user.rol.descripcion if user.rol else None, 'is_active': user.is_active, 'email': user.email}
        user = serializer.save()
        audit_changes(request.user, user, before)
        return Response(serializer.data)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        lock_administration()
        request.user.refresh_from_db()
        self.check_permissions(request)
        user = get_object_or_404(User.objects.select_for_update(), pk=kwargs['pk'])
        ensure_deletable(user)
        if user.pk == request.user.pk:
            raise serializers.ValidationError('No podés eliminar tu propia cuenta. Usá otro administrador.')
        audit(request.user, user, 'USUARIO_ELIMINADO')
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
