import { apiBaseUrl } from "./services/api";
export const BASE_URL = apiBaseUrl;
export const API_ROUTES = {
    ROLES: BASE_URL + 'roles/',
    USUARIOS: BASE_URL + 'users/',
    RETENCIONES: BASE_URL + 'constancias-retencion/',
    DECLARACIONES: BASE_URL + 'declaraciones/',
    PROVEEDORES: BASE_URL + 'proveedores/',
    PROVINCIAS: BASE_URL + 'provincias/',
    DEPARTAMENTOS: BASE_URL + 'departamentos/',
    LOCALIDADES: BASE_URL + 'localidades/',
    RUBROS: BASE_URL + 'rubros/',
    IMPUESTOS: BASE_URL + 'impuestos/',
    TASAS_RETENCION: BASE_URL + 'tasas-retencion/',
    TASAS_IMPUESTO: BASE_URL + 'tasas-impuesto/',
    PROVEEDOR_IMPUESTO: BASE_URL + 'proveedor-impuestos/',
    AUDITORIA_DECLARACIONES: BASE_URL + 'auditoria-declaraciones/',
    AUDITORIA_CONSTANCIAS: BASE_URL + 'auditoria-constancias/',
    AUDITORIA_UNIFICADA: BASE_URL + 'auditoria-reporte/'
}
