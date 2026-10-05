from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from usuarios.models import User as Usuario
from django.utils.translation import gettext_lazy as _
from ..forms import UserChangeForm, UserCreationForm


@admin.register(Usuario) 
class UsuarioAdmin(auth_admin.UserAdmin):

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
