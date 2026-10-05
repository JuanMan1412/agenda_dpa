import axios from "axios";
import AuthenticationHelper from "../shared/helpers/authenticationHelper";

const raw = String(import.meta.env.VITE_API_URL || window.location.origin).trim().replace(/\/+$/, "");
export const apiBaseUrl = raw.endsWith("/api") ? `${raw}/` : `${raw}/api/`;
const api = axios.create({ baseURL: apiBaseUrl });

api.interceptors.request.use((config) => {
  const token = AuthenticationHelper.getJwtToken();
  if (token && !config.publicRequest) config.headers.set("Authorization", `Bearer ${token}`);
  return config;
});
api.interceptors.response.use((response) => response, (error) => {
  if (error.response?.status === 401 && !error.config?.publicRequest) {
    AuthenticationHelper.logout();
    if (window.location.pathname !== "/portal-access") window.location.replace("/portal-access");
  }
  return Promise.reject(error);
});

export async function portalAccess(token) {
  const { data } = await api.post("auth/portal-access/", { token }, { publicRequest: true });
  return data;
}
export async function getMyPermissions() {
  const { data } = await api.get("me/permisos/");
  return data;
}
export default api;
