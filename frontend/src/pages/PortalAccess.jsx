import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { portalAccess } from "../services/api";
import AuthenticationHelper from "../shared/helpers/authenticationHelper";
import { buildPortalLoginHref } from "../shared/helpers/portalUrls";

const tokenKeys = ["portal_token", "token", "access_token", "jwt", "auth_token"];
function readToken() {
  for (const params of [new URLSearchParams(window.location.search), new URLSearchParams(window.location.hash.slice(1))]) {
    for (const key of tokenKeys) {
      const value = params.get(key);
      if (value?.trim()) return value.trim();
    }
  }
  return "";
}

export default function PortalAccess() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [token] = useState(readToken);
  const [result, setResult] = useState(null);
  const exchange = useRef(null);
  let loginHref = "";
  let configError = "";
  try { loginHref = buildPortalLoginHref(); } catch { configError = "Revisá la configuración de acceso al portal."; }

  useEffect(() => {
    let active = true;
    // Quitar la credencial incluso si el canje falla. No conservar snapshots de la URL.
    window.history.replaceState(null, "", window.location.pathname);
    if (!token) return () => { active = false; };
    if (!exchange.current) {
      AuthenticationHelper.logout();
      queryClient.clear();
      exchange.current = portalAccess(token);
    }
    exchange.current.then((payload) => {
      if (!active) return;
      if (!payload?.access || !payload?.refresh || !payload?.user) throw new Error("Respuesta inválida del sistema.");
      AuthenticationHelper.storePortalSession(payload);
      navigate("/", { replace: true });
    }).catch((error) => {
      if (!active) return;
      AuthenticationHelper.logout();
      const detail = error.response?.data?.detail;
      setResult(typeof detail === "string" ? detail : "No se pudo validar el acceso desde el portal.");
    });
    return () => { active = false; };
  }, [token, navigate, queryClient]);

  const message = result || configError || (!token ? "Ingresá desde el Portal DPA para acceder a la agenda." : "Validando acceso desde el portal...");
  return <main className="portal-access">
    <h1>Registro de Expedientes DPA</h1>
    <h2>Acceso desde el portal</h2>
    <p role={result ? "alert" : "status"}>{message}</p>
    {(!token || result) && loginHref && <a className="portal-link" href={loginHref}>Ir al portal</a>}
  </main>;
}
