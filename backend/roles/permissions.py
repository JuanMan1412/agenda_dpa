from rest_framework.permissions import BasePermission, SAFE_METHODS


def access(write=False, cancel=False):
    return {'ver': True, 'escribir': write, 'crear_registro': write, 'editar_registro': write, 'registrar_sigedoc': write, 'anular_registro': cancel}

SECTION_ACCESS_MATRIX = {
    'CONSULTOR': {'agenda': access(), 'pendientes_sigedoc': {'ver': False}, 'usuarios': {'ver': False}},
    'ADMINISTRATIVO': {'agenda': access(True), 'pendientes_sigedoc': {'ver': True}, 'usuarios': {'ver': False}},
    'ADMINISTRADOR': {'agenda': access(True, True), 'pendientes_sigedoc': {'ver': True}, 'usuarios': {'ver': True, 'escribir': True}},
}


def get_user_permissions(user):
    role = user.rol.descripcion if user.is_active and user.rol and user.rol.estado else ''
    denied = {key: False for key in access()}
    return role, SECTION_ACCESS_MATRIX.get(role, {'agenda': denied})


class AgendaPermission(BasePermission):
    message = 'Tu rol local no permite realizar esta operacion en el Registro de Expedientes.'
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated: return False
        _, sections = get_user_permissions(request.user)
        operation = getattr(view, 'operacion', 'ver' if request.method in SAFE_METHODS else 'crear_registro')
        return bool(sections['agenda'].get(operation, False))


class SectionPermission(BasePermission):
    message = 'No tenés permisos para acceder a esta sección.'
    section = ''

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        _, sections = get_user_permissions(request.user)
        return bool(sections.get(self.section, {}).get('ver'))


class CanManageUsers(SectionPermission):
    section = 'usuarios'


class CanManageSigedoc(SectionPermission):
    section = 'pendientes_sigedoc'
