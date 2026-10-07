import { useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import AuthenticationHelper from "../../shared/helpers/authenticationHelper";
import { buildPortalLogoutHref } from "../../shared/helpers/portalUrls";
import { usePermissions } from "../../contexts/usePermissions";
import logoDpa from "../../images/logo.png";

export default function Topbar() {
  const [profileOpen, setProfileOpen] = useState(false);
  const [logoutLoading, setLogoutLoading] = useState(false);
  const [error, setError] = useState("");
  const pending = useRef(false);
  const queryClient = useQueryClient();
  const { rol } = usePermissions();
  const user = AuthenticationHelper.getUser();
  const name = user?.nombre_completo || [user?.nombre, user?.apellido].filter(Boolean).join(" ") || user?.username || "Usuario";

  function handleLogout() {
    if (pending.current) return;
    let target;
    try { target = buildPortalLogoutHref(); } catch {
      setError("No se pudo cerrar la sesión central: revisá VITE_PORTAL_BASE_URL.");
      return;
    }
    pending.current = true;
    setLogoutLoading(true);
    setProfileOpen(false);
    queryClient.clear();
    AuthenticationHelper.logout(() => window.location.replace(target));
  }

  return <header className="topbar">
    <div className="brand"><img className="brand-logo" src={logoDpa} alt="DPA" /><strong>Registro de Expedientes</strong></div>
    <div className="profile">
      <button type="button" onClick={() => setProfileOpen((open) => !open)} aria-expanded={profileOpen} aria-controls="profile-menu">{name} ▾</button>
      {profileOpen && <div id="profile-menu" className="profile-menu">
        <p>{user?.username}</p><p>Rol: {rol || "Sin permisos"}</p>
        <button type="button" onClick={handleLogout} disabled={logoutLoading}>{logoutLoading ? "Cerrando sesión..." : "Cerrar sesión"}</button>
      </div>}
      {error && <p role="alert">{error}</p>}
    </div>
  </header>;
}
