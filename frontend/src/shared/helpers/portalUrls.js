function configuredUrl(value, label) {
  if (!value?.trim()) throw new Error(`Falta configurar ${label}.`);
  const url = new URL(value);
  if (!["http:", "https:"].includes(url.protocol)) throw new Error(`${label} debe ser una URL HTTP o HTTPS.`);
  return url;
}

export function buildPortalLoginHref() {
  const login = configuredUrl(import.meta.env.VITE_PORTAL_LOGIN_URL, "VITE_PORTAL_LOGIN_URL");
  if (login.pathname === "/") login.pathname = "/login";
  login.searchParams.set("redirect", new URL("/portal-access", window.location.origin).toString());
  return login.toString();
}

export function buildPortalLogoutHref() {
  const base = configuredUrl(import.meta.env.VITE_PORTAL_BASE_URL, "VITE_PORTAL_BASE_URL");
  base.pathname = `${base.pathname.replace(/\/+$/, "")}/logout`;
  base.search = "";
  base.hash = "";
  return base.toString();
}
