class AuthenticationHelper {
  static isUserAuthenticated() {
    return Boolean(sessionStorage.getItem("jwtToken"));
  }

  static isJwtTokenStored() {
    return Boolean(AuthenticationHelper.getJwtToken());
  }

  static logout(callback = () => {}) {
    sessionStorage.removeItem("jwtToken");
    sessionStorage.removeItem("refreshToken");
    sessionStorage.removeItem("portalRefreshToken");
    sessionStorage.removeItem("portal_refresh_token");
    localStorage.removeItem("portal_refresh_token");
    sessionStorage.removeItem("user");
    sessionStorage.removeItem("rolUser");
    sessionStorage.removeItem("hasChangedPassword");
    sessionStorage.removeItem("userPermissions");

    // Backward-compatible cleanup for previous storage keys still present in browsers.
    sessionStorage.removeItem("access");
    sessionStorage.removeItem("refresh");
    sessionStorage.removeItem("rol");
    sessionStorage.removeItem("has_changed_password");

    callback();
  }

  static getJwtToken() {
    return sessionStorage.getItem("jwtToken");
  }

  static storeJwtToken(jwtToken) {
    const value = String(jwtToken || "").replace(/^Bearer\s+/i, "");
    sessionStorage.setItem("jwtToken", value);
  }

  static getRefreshToken() {
    return sessionStorage.getItem("refreshToken");
  }

  static storeRefreshToken(refreshToken) {
    sessionStorage.setItem("refreshToken", refreshToken || "");
  }

  static storePortalRefreshToken(refreshToken) {
    if (!refreshToken) {
      return;
    }

    sessionStorage.setItem("portalRefreshToken", refreshToken);
    localStorage.setItem("portal_refresh_token", refreshToken);
  }

  static removeJwtToken() {
    sessionStorage.removeItem("jwtToken");
  }

  static removeUser() {
    sessionStorage.removeItem("user");
  }

  static removeRol() {
    sessionStorage.removeItem("rolUser");
  }

  static removeHasChangedPassword() {
    sessionStorage.removeItem("hasChangedPassword");
  }

  static storeUser(user) {
    sessionStorage.setItem("user", JSON.stringify(user));
  }

  static getUser() {
    try {
      return sessionStorage.getItem("user") ? JSON.parse(sessionStorage.getItem("user")) : null;
    } catch {
      return null;
    }
  }

  static storeRol(rol) {
    sessionStorage.setItem("rolUser", rol || "");
  }

  static getRol() {
    return sessionStorage.getItem("rolUser") || "";
  }

  static storeHasChangedPassword(hasChangedPassword) {
    sessionStorage.setItem("hasChangedPassword", String(Boolean(hasChangedPassword)));
  }

  static getHasChangedPassword() {
    return sessionStorage.getItem("hasChangedPassword") === "true";
  }

  static storeUserPermissions(permissions) {
    sessionStorage.setItem("userPermissions", JSON.stringify(permissions || []));
  }

  static storePortalSession(payload, portalRefreshToken = "") {
    AuthenticationHelper.logout();
    AuthenticationHelper.storeJwtToken(payload.access);
    AuthenticationHelper.storeRefreshToken(payload.refresh);
    AuthenticationHelper.storeUser(payload.user);
    AuthenticationHelper.storeRol(payload.rol);
    AuthenticationHelper.storeHasChangedPassword(payload.has_changed_password);
    AuthenticationHelper.storeUserPermissions(payload.userPermissions || payload.user_permissions || []);

    if (portalRefreshToken) {
      AuthenticationHelper.storePortalRefreshToken(portalRefreshToken);
    }
  }
}

export default AuthenticationHelper;
