from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from usuarios.models import User as Usuario
from django.utils.translation import gettext_lazy as _
from ..forms import UserChangeForm, UserCreationForm
from django.db import transaction
from rest_framework.exceptions import ValidationError as ApiValidationError
from roles.permissions import get_user_permissions
from usuarios.administration import audit, audit_changes, ensure_deletable, lock_administration


@admin.register(Usuario) 
class UsuarioAdmin(auth_admin.UserAdmin):

    def has_module_permission(self, request):
        return bool(get_user_permissions(request.user)[1].get('usuarios', {}).get('ver')) and super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request) and super().has_view_permission(request, obj)

    def has_add_permission(self, request):
        return self.has_module_permission(request) and super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request) and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if not self.has_module_permission(request) or not super().has_delete_permission(request, obj):
            return False
        if obj:
            if obj.pk == request.user.pk:
                return False
            try:
                ensure_deletable(obj)
            except ApiValidationError:
                return False
        return True

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if obj and obj.portal_user_id:
            fields += ['username', 'nombre', 'apellido', 'nombre_completo', 'portal_user_id']
        return fields

    @transaction.atomic
    def changeform_view(self, request, *args, **kwargs):
        if request.method == 'POST':
            lock_administration()
            request.user.refresh_from_db()
        return super().changeform_view(request, *args, **kwargs)

    @transaction.atomic
    def delete_view(self, request, *args, **kwargs):
        if request.method == 'POST':
            lock_administration()
            request.user.refresh_from_db()
        return super().delete_view(request, *args, **kwargs)

    def save_model(self, request, obj, form, change):
        old = Usuario.objects.get(pk=obj.pk) if change else None
        super().save_model(request, obj, form, change)
        if old:
            audit_changes(request.user, obj, {'rol': old.rol.descripcion if old.rol else None, 'is_active': old.is_active, 'email': old.email})
        else:
            audit(request.user, obj, 'USUARIO_CREADO')

    def delete_model(self, request, obj):
        ensure_deletable(obj)
        audit(request.user, obj, 'USUARIO_ELIMINADO')
        super().delete_model(request, obj)

    form = UserChangeForm
    add_form = UserCreationForm
    list_display = ['id','username','is_active','nombre','apellido','documento','is_staff','rol','date_joined', 'last_login', 'has_changed_password','last_password_change']
    list_filter = ['is_active','username','documento']
    search_fields = ['username','nombre','apellido','rol__descripcion','portal_user_id']
    ordering = ['username']
    
    def get_fieldsets(self, request, obj=None):
            if not obj:
                return (
                        (None, {"fields": ("username", "password1", "password2")}),
                        ("Datos del Empleado", {"fields": ("nombre", "apellido", "documento", "rol")}),
                        (
                            _("Permissions"),
                            {
                                "fields": (
                                    "is_active",
                                    "is_staff",
                                    "is_superuser",
                                    "groups",
                                    "user_permissions",
                                ),
                            },
                        ),
                        )
            else:
                return (
                    (None, {"fields": ("username", "password","date_joined")}),
                    ("Empleado", {"fields": ("nombre", "apellido", "nombre_completo", "documento","rol", "portal_user_id")}),
                    ("Password", {"fields": ("has_changed_password","last_password_change")}),
                    (
                        _("Permissions"),
                        {
                            "fields": (
                                "is_active",
                                "is_staff",
                                "is_superuser",
                                "groups",
                                "user_permissions",
                            ),
                        },
                    ),
                )
