export const normalizeRole = (role = "") =>
  String(role)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim()
    .toUpperCase();

export const ROLES = {
  ADMINISTRADOR: "ADMINISTRADOR",
  GESTOR_COMBUSTIBLE: "GESTOR DE COMBUSTIBLE Y FLOTA",
  ADMINISTRATIVO_COMBUSTIBLE: "ADMINISTRATIVO DE COMBUSTIBLE",
  ENTREGA_VALES: "ENTREGA DE VALES",
  SUPERVISOR_COMBUSTIBLE: "SUPERVISOR DE COMBUSTIBLE",
  GESTOR_VIAJES: "GESTOR DE VIAJES",
  GESTOR_FLOTA: "GESTOR DE FLOTA",
  OPERADOR_GPS: "OPERADOR GPS",
  CONSULTOR: "CONSULTOR",
};

export const isAdministradorRole = (role) => normalizeRole(role) === ROLES.ADMINISTRADOR;

export const canManageSystem = (role) =>
  [
    ROLES.ADMINISTRADOR,
    ROLES.GESTOR_COMBUSTIBLE,
    ROLES.SUPERVISOR_COMBUSTIBLE,
    ROLES.GESTOR_VIAJES,
    ROLES.GESTOR_FLOTA,
    ROLES.OPERADOR_GPS,
  ].includes(normalizeRole(role));

export const canViewSystem = (role) => canManageSystem(role) || normalizeRole(role) === ROLES.CONSULTOR;

export const canAccessPlanillasCombustible = (role) =>
  [ROLES.ADMINISTRADOR, ROLES.GESTOR_COMBUSTIBLE].includes(normalizeRole(role));
