from django.contrib import admin
from .models import Rol
from .permissions import get_user_permissions

@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ['id','descripcion','estado']
    search_fields = ['descripcion']
    list_filter = ['descripcion']
    list_per_page = 10
    readonly_fields = ['descripcion', 'estado', 'fecha_creacion', 'fecha_modificacion']

    def has_module_permission(self, request):
        return bool(get_user_permissions(request.user)[1].get('usuarios', {}).get('ver')) and super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request) and super().has_view_permission(request, obj)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
