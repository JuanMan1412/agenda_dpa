from django.contrib.admin import AdminSite
from roles.permissions import get_user_permissions


class RegistroAdminSite(AdminSite):
    def has_permission(self, request):
        if not super().has_permission(request):
            return False
        _, sections = get_user_permissions(request.user)
        return bool(sections.get('usuarios', {}).get('ver'))
