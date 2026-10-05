import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useLocation } from "react-router-dom";

import { getMyPermissions } from "../services/api";
import AuthenticationHelper from "../shared/helpers/authenticationHelper";

import { PermissionsContext } from "./usePermissions";

function defaultSectionAccess() {
  return { ver: false, escribir: false };
}

export function PermissionsProvider({ children }) {
  const location = useLocation();
  const isAuthenticated = AuthenticationHelper.isUserAuthenticated();
  const permissionsQuery = useQuery({
    queryKey: ["me", "permisos", AuthenticationHelper.getUser()?.id],
    queryFn: getMyPermissions,
    enabled: isAuthenticated && location.pathname !== "/portal-access",
    refetchOnMount: "always",
  });

  const value = useMemo(() => {
    const permissions = permissionsQuery.data?.secciones || {};
    const permissionsLoaded = Boolean(permissionsQuery.data?.secciones);
    const isLoading = isAuthenticated && (permissionsQuery.isLoading || permissionsQuery.isPending);

    return {
      rol: permissionsQuery.data?.rol || "",
      permissions,
      permissionsLoaded,
      isLoading,
      isError: permissionsQuery.isError,
      getSectionAccess: (section) => permissions[section] || defaultSectionAccess(),
      canViewSection: (section) => Boolean(permissions[section]?.ver),
      canWriteSection: (section) => Boolean(permissions[section]?.escribir),
    };
  }, [isAuthenticated, permissionsQuery.data, permissionsQuery.isError, permissionsQuery.isLoading, permissionsQuery.isPending]);

  return <PermissionsContext.Provider value={value}>{children}</PermissionsContext.Provider>;
}
