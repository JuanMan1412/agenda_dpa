from rest_framework.permissions import BasePermission, SAFE_METHODS


def access(write=False, cancel=False):
    return {'ver': True, 'escribir': write, 'crear_registro': write, 'registrar_sigedoc': write, 'anular_registro': cancel}

SECTION_ACCESS_MATRIX = {
    'CONSULTOR': {'agenda': access()},
    'ADMINISTRATIVO': {'agenda': access(True)},
    'ADMINISTRADOR': {'agenda': access(True, True)},
}


def get_user_permissions(user):
    role = user.rol.descripcion if user.rol and user.rol.estado else ''
    denied = {key: False for key in access()}
    return role, SECTION_ACCESS_MATRIX.get(role, {'agenda': denied})


class AgendaPermission(BasePermission):
    message = 'Tu rol local no permite realizar esta operacion en el Registro de Expedientes.'
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated: return False
        _, sections = get_user_permissions(request.user)
        operation = getattr(view, 'operacion', 'ver' if request.method in SAFE_METHODS else 'crear_registro')
        return bool(sections['agenda'].get(operation, False))
