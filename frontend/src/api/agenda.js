import axios from "axios";

axios.defaults.xsrfCookieName = "csrftoken";
axios.defaults.xsrfHeaderName = "X-CSRFToken";

const api = axios.create({
  baseURL: "http://localhost:8001/api/",
  withCredentials: true,
});

export async function listarAgenda() {
  const { data } = await api.get("agenda/");
  return data;
}

export async function cargarManual(letra) {
  const { data } = await api.post("agenda/manual/", { letra });
  return data;
}

export default api;