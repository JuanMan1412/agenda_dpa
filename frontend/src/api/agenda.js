import api from '../services/api';
export async function listarAgenda(params = {}, signal) {
  const { data } = await api.get('expedientes/', { params, signal }); return data;
}
export async function resumenAgenda(anio, signal) {
  const { data } = await api.get('expedientes/resumen/', { params: anio ? { anio } : {}, signal }); return data;
}
export async function cargarManual(payload, idempotencia) {
  const { data } = await api.post('expedientes/manual/', payload, { headers: { 'Idempotency-Key': idempotencia } }); return data;
}
export async function detalleAgenda(id, signal) {
  const { data } = await api.get(`expedientes/${id}/`, { signal }); return data;
}
export async function marcarSigedoc(id) {
  const { data } = await api.post(`expedientes/${id}/registrar-sigedoc/`, { confirmar: true }); return data;
}
export async function anularExpediente(id, motivo) {
  const { data } = await api.post(`expedientes/${id}/anular/`, { motivo }); return data;
}
export default api;
