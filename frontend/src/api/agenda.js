import axios from "axios";

const apiBaseUrl = import.meta.env.VITE_API_URL;
if (!apiBaseUrl) throw new Error("Falta definir VITE_API_URL en el archivo .env del frontend.");

const api = axios.create({ baseURL: apiBaseUrl.endsWith("/") ? apiBaseUrl : `${apiBaseUrl}/`, withCredentials: true });

export async function listarAgenda({ estado, buscar } = {}) {
  const { data } = await api.get("agenda/", { params: { estado: estado || undefined, buscar: buscar || undefined } });
  return data;
}
export async function obtenerEstadisticas() { const { data } = await api.get("agenda/estadisticas/"); return data; }
export async function cargarManual({ letra, asunto, causante }) { const { data } = await api.post("agenda/manual/", { letra, asunto, causante }); return data; }
export async function marcarComoCargado(id, referencia_externa) { const { data } = await api.post(`agenda/${id}/cargar/`, { referencia_externa }); return data; }
export default api;
