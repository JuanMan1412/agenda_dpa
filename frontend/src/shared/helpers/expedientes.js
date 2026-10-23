export function fecha(value, dateOnly = false) {
  if (!value) return '—';
  return new Intl.DateTimeFormat('es-AR', {
    timeZone: 'America/Argentina/Buenos_Aires', dateStyle: 'short',
    ...(dateOnly ? {} : { timeStyle: 'short', hourCycle: 'h23' }),
  }).format(new Date(value));
}

export function origen(value) {
  if (value === 'MESA_ENTRADA' || value === 'manual') return 'Mesa de Entrada';
  if (value === 'SISTEMA_TRAMITES') return 'Sistema de Trámites';
  if (value === 'SISTEMA_LEGADO' || value === 'automatico') return 'Integración anterior';
  return value?.replace(/^SISTEMA_/, 'Sistema ').replaceAll('_', ' ') || '—';
}

export function errorMessage(error, fallback = 'No se pudo completar la operación.') {
  if (error?.response?.status === 403) return 'Tu rol no permite realizar esta operación.';
  const data = error?.response?.data;
  if (typeof data?.detail === 'string') return data.detail;
  if (data && typeof data === 'object') {
    return Object.entries(data).map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(' ') : value}`).join(' · ');
  }
  return fallback;
}
