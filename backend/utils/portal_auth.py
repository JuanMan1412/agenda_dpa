from django.conf import settings
from rest_framework import permissions
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTStatelessUserAuthentication


PORTAL_ROLE_ADMINISTRADOR = "ADMINISTRADOR"
PORTAL_ROLE_GESTOR_COMBUSTIBLE = "GESTOR DE COMBUSTIBLE Y FLOTA"
PORTAL_ROLE_ADMINISTRATIVO_COMBUSTIBLE = "ADMINISTRATIVO DE COMBUSTIBLE"
PORTAL_ROLE_ENTREGA_VALES = "ENTREGA DE VALES"
PORTAL_ROLE_SUPERVISOR_COMBUSTIBLE = "SUPERVISOR DE COMBUSTIBLE"
PORTAL_ROLE_GESTOR_VIAJES = "GESTOR DE VIAJES"
PORTAL_ROLE_OPERADOR_GPS = "OPERADOR GPS"
PORTAL_ROLE_CONSULTOR = "CONSULTOR"

SECTION_ACCESS_MATRIX = {
    PORTAL_ROLE_ADMINISTRADOR: {
        "inicio": {"ver": True, "escribir": True},
        "vehiculos": {"ver": True, "escribir": True},
        "empleados": {"ver": True, "escribir": True},
        "asignaciones": {"ver": True, "escribir": True},
        "mantenimiento": {"ver": True, "escribir": True},
        "combustible": {"ver": True, "escribir": True},
        "reposiciones": {"ver": True, "escribir": True},
        "reportes": {"ver": True, "escribir": True},
        "registro-salidas": {"ver": True, "escribir": True},
        "visor-gps": {"ver": True, "escribir": True},
        "usuarios": {"ver": True, "escribir": True},
    },
    PORTAL_ROLE_GESTOR_COMBUSTIBLE: {
        "inicio": {"ver": True, "escribir": True},
        "vehiculos": {"ver": True, "escribir": True},
        "empleados": {"ver": False, "escribir": False},
        "asignaciones": {"ver": False, "escribir": False},
        "mantenimiento": {"ver": True, "escribir": True},
        "combustible": {"ver": True, "escribir": True},
        "reposiciones": {"ver": False, "escribir": False},
        "reportes": {"ver": False, "escribir": False},
        "registro-salidas": {"ver": False, "escribir": False},
        "visor-gps": {"ver": False, "escribir": False},
        "usuarios": {"ver": False, "escribir": False},
    },
    PORTAL_ROLE_ADMINISTRATIVO_COMBUSTIBLE: {
        "inicio": {"ver": True, "escribir": True},
        "vehiculos": {"ver": False, "escribir": False},
        "empleados": {"ver": False, "escribir": False},
        "asignaciones": {"ver": False, "escribir": False},
        "mantenimiento": {"ver": False, "escribir": False},
        "combustible": {"ver": True, "escribir": True},
        "reposiciones": {"ver": False, "escribir": False},
        "reportes": {"ver": False, "escribir": False},
        "registro-salidas": {"ver": False, "escribir": False},
        "visor-gps": {"ver": False, "escribir": False},
        "usuarios": {"ver": False, "escribir": False},
    },
    PORTAL_ROLE_ENTREGA_VALES: {
        "inicio": {"ver": True, "escribir": True},
        "vehiculos": {"ver": False, "escribir": False},
        "empleados": {"ver": False, "escribir": False},
        "asignaciones": {"ver": False, "escribir": False},
        "mantenimiento": {"ver": False, "escribir": False},
        "combustible": {"ver": True, "escribir": True},
        "reposiciones": {"ver": False, "escribir": False},
        "reportes": {"ver": False, "escribir": False},
        "registro-salidas": {"ver": False, "escribir": False},
        "visor-gps": {"ver": False, "escribir": False},
        "usuarios": {"ver": False, "escribir": False},
    },
    PORTAL_ROLE_SUPERVISOR_COMBUSTIBLE: {
        "inicio": {"ver": True, "escribir": True},
        "vehiculos": {"ver": False, "escribir": False},
        "empleados": {"ver": False, "escribir": False},
        "asignaciones": {"ver": False, "escribir": False},
        "mantenimiento": {"ver": False, "escribir": False},
        "combustible": {"ver": True, "escribir": True},
        "reposiciones": {"ver": True, "escribir": True},
        "reportes": {"ver": True, "escribir": True},
        "registro-salidas": {"ver": False, "escribir": False},
        "visor-gps": {"ver": False, "escribir": False},
        "usuarios": {"ver": False, "escribir": False},
    },
    PORTAL_ROLE_GESTOR_VIAJES: {
        "inicio": {"ver": True, "escribir": True},
        "vehiculos": {"ver": False, "escribir": False},
        "empleados": {"ver": False, "escribir": False},
        "asignaciones": {"ver": True, "escribir": True},
        "mantenimiento": {"ver": False, "escribir": False},
        "combustible": {"ver": False, "escribir": False},
        "reposiciones": {"ver": False, "escribir": False},
        "reportes": {"ver": False, "escribir": False},
        "registro-salidas": {"ver": True, "escribir": True},
        "visor-gps": {"ver": False, "escribir": False},
        "usuarios": {"ver": False, "escribir": False},
    },
    PORTAL_ROLE_OPERADOR_GPS: {
        "inicio": {"ver": True, "escribir": True},
        "vehiculos": {"ver": False, "escribir": False},
        "empleados": {"ver": False, "escribir": False},
        "asignaciones": {"ver": False, "escribir": False},
        "mantenimiento": {"ver": False, "escribir": False},
        "combustible": {"ver": False, "escribir": False},
        "reposiciones": {"ver": False, "escribir": False},
        "reportes": {"ver": False, "escribir": False},
        "registro-salidas": {"ver": False, "escribir": False},
        "visor-gps": {"ver": True, "escribir": True},
        "usuarios": {"ver": False, "escribir": False},
    },
    PORTAL_ROLE_CONSULTOR: {
        "inicio": {"ver": True, "escribir": False},
        "vehiculos": {"ver": True, "escribir": False},
        "empleados": {"ver": True, "escribir": False},
        "asignaciones": {"ver": True, "escribir": False},
        "mantenimiento": {"ver": True, "escribir": False},
        "combustible": {"ver": True, "escribir": False},
        "reposiciones": {"ver": True, "escribir": False},
        "reportes": {"ver": True, "escribir": False},
        "registro-salidas": {"ver": True, "escribir": False},
        "visor-gps": {"ver": True, "escribir": False},
        "usuarios": {"ver": False, "escribir": False},
    },
}
PORTAL_KNOWN_ROLES = set(SECTION_ACCESS_MATRIX.keys())
PORTAL_ROLE_ADMINISTRATIVO = {role for role, sections in SECTION_ACCESS_MATRIX.items() if any(section["escribir"] for section in sections.values())}
PORTAL_ROLE_CONSULTA = {role for role, sections in SECTION_ACCESS_MATRIX.items() if any(section["ver"] for section in sections.values())}
SECTION_CODE_ALIASES = {
    "dashboard": "inicio",
    "inicio": "inicio",
    "home": "inicio",
    "salidas": "registro-salidas",
    "registro_salidas": "registro-salidas",
    "registro-salidas": "registro-salidas",
    "registro salidas": "registro-salidas",
    "visor_gps": "visor-gps",
    "visor-gps": "visor-gps",
    "usuarios": "usuarios",
}
ROLE_NAME_ALIASES = {
    "GESTOR DE FLOTA": PORTAL_ROLE_GESTOR_COMBUSTIBLE,
    "GESTOR DE COMBUSTIBLE": PORTAL_ROLE_GESTOR_COMBUSTIBLE,
}


def normalize_sistemas_claim(sistemas):
    if sistemas is None:
        return []
    if isinstance(sistemas, str):
        return [item.strip() for item in sistemas.split(",") if item.strip()]
    if isinstance(sistemas, (list, tuple, set)):
        return [str(item).strip() for item in sistemas if str(item).strip()]
    return []


def normalize_system_code(value):
    return str(value or "").strip().lower()


def normalize_role_name(role):
    normalized = str(role or "").strip().upper()
    return ROLE_NAME_ALIASES.get(normalized, normalized)


def normalize_section_code(section_code):
    normalized = str(section_code or "").strip().lower()
    if not normalized:
        return ""
    return SECTION_CODE_ALIASES.get(normalized, normalized)


def get_section_permissions_for_role(role):
    normalized_role = normalize_role_name(role)
    base_permissions = {section: {"ver": False, "escribir": False} for section in SECTION_ACCESS_MATRIX[PORTAL_ROLE_ADMINISTRADOR]}
    role_permissions = SECTION_ACCESS_MATRIX.get(normalized_role, {})

    for section, access in role_permissions.items():
        base_permissions[section] = {
            "ver": bool(access.get("ver")),
            "escribir": bool(access.get("escribir")),
        }

    return base_permissions


def get_user_section_permissions(request):
    return get_section_permissions_for_role(get_request_role(request))


def can_access_section(role, section_code, operation="view"):
    section = normalize_section_code(section_code)
    permissions_map = get_section_permissions_for_role(role)
    access = permissions_map.get(section, {"ver": False, "escribir": False})

    if operation in {"view", "read", "list", "retrieve", "export"}:
        return access["ver"]
    if operation in {"write", "create", "update", "partial_update", "destroy", "delete", "change_status"}:
        return access["escribir"]
    return False


def get_request_role(request):
    user = getattr(request, "user", None)
    if user and getattr(user, "is_authenticated", False) and getattr(user, "rol_id", None):
        return normalize_role_name(getattr(user.rol, "descripcion", ""))

    auth = getattr(request, "auth", None)
    if isinstance(auth, dict) or hasattr(auth, "get"):
        return normalize_role_name(auth.get("rol"))

    return ""


class PortalJWTAuthentication(JWTStatelessUserAuthentication):
    """
    Acepta el JWT del portal y exige que el claim `sistemas`
    incluya el codigo del sistema actual.
    """

    def get_validated_token(self, raw_token):
        validated_token = super().get_validated_token(raw_token)
        sistemas = {normalize_system_code(item) for item in normalize_sistemas_claim(validated_token.get("sistemas"))}
        system_code = normalize_system_code(getattr(settings, "PORTAL_SYSTEM_CODE", ""))

        if system_code and system_code not in sistemas:
            raise AuthenticationFailed("El token no tiene acceso a este sistema.")

        return validated_token


class TieneAccesoAlSistema(permissions.BasePermission):
    sistema_requerido = None

    def has_permission(self, request, view):
        if not getattr(settings, "ACCESS_CONTROL_ENABLED", False):
            return True

        auth = getattr(request, "auth", None)
        if not request.user or not request.user.is_authenticated or auth is None:
            return False

        sistema_requerido = getattr(view, "sistema_requerido", None) or self.sistema_requerido or getattr(settings, "PORTAL_SYSTEM_CODE", "")
        sistemas = {normalize_system_code(item) for item in normalize_sistemas_claim(auth.get("sistemas", []))} if hasattr(auth, "get") else set()
        return not sistema_requerido or sistema_requerido in sistemas


class EsAdministrador(permissions.BasePermission):
    def has_permission(self, request, view):
        if not getattr(settings, "ACCESS_CONTROL_ENABLED", False):
            return True
        return bool(request.user and request.user.is_authenticated and get_request_role(request) == PORTAL_ROLE_ADMINISTRADOR)


class EsAdministrativo(permissions.BasePermission):
    def has_permission(self, request, view):
        if not getattr(settings, "ACCESS_CONTROL_ENABLED", False):
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        return get_request_role(request) in PORTAL_ROLE_ADMINISTRATIVO


class EsConsultor(permissions.BasePermission):
    def has_permission(self, request, view):
        if not getattr(settings, "ACCESS_CONTROL_ENABLED", False):
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        return get_request_role(request) in PORTAL_ROLE_CONSULTA


class PortalPermissionMixin:
    """
    Mantiene compatibilidad con vistas protegidas por acceso al sistema.
    """

    sistema_requerido = None
    permission_action_map = {
        "list": [EsConsultor],
        "retrieve": [EsConsultor],
        "create": [EsAdministrativo],
        "update": [EsAdministrativo],
        "partial_update": [EsAdministrativo],
        "destroy": [EsAdministrador],
    }

    def get_permissions(self):
        permission_classes = [TieneAccesoAlSistema]
        permission_classes.extend(self.permission_action_map.get(getattr(self, "action", None), [EsConsultor]))
        return [permission() for permission in permission_classes]


class RolePermissionByActionMixin:
    """
    Permite declarar permisos por accion usando descripciones de rol.
    """

    role_permission_map = {
        "list": PORTAL_KNOWN_ROLES,
        "retrieve": PORTAL_KNOWN_ROLES,
        "create": PORTAL_KNOWN_ROLES,
        "update": PORTAL_KNOWN_ROLES,
        "partial_update": PORTAL_KNOWN_ROLES,
        "destroy": PORTAL_KNOWN_ROLES,
    }

    def get_permissions(self):
        base_permissions = super().get_permissions()
        if not getattr(settings, "ACCESS_CONTROL_ENABLED", False):
            return base_permissions
        return base_permissions + [RolePermissionByAction()]


class RolePermissionByAction(permissions.BasePermission):
    def has_permission(self, request, view):
        if not getattr(settings, "ACCESS_CONTROL_ENABLED", False):
            return True

        action = getattr(view, "action", None)
        role_map = getattr(view, "role_permission_map", {})
        allowed_roles = role_map.get(action)

        if allowed_roles is None:
            return True

        return get_request_role(request) in {normalize_role_name(role) for role in allowed_roles}


def require_section_access(request, section_code, operation="view"):
    if not getattr(settings, "ACCESS_CONTROL_ENABLED", False):
        return True

    return can_access_section(get_request_role(request), section_code, operation)


class HasSectionAccess(permissions.BasePermission):
    def has_permission(self, request, view):
        if not getattr(settings, "ACCESS_CONTROL_ENABLED", False):
            return True

        operation = "view" if request.method in permissions.SAFE_METHODS else "write"
        section_code = view.get_section_code(request) if hasattr(view, "get_section_code") else getattr(view, "section_code", None)
        return require_section_access(request, section_code, operation)


class AccessControlEnabledOrAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        if not getattr(settings, "ACCESS_CONTROL_ENABLED", False):
            return True
        return bool(request.user and request.user.is_authenticated)
