import { Navigate } from "react-router-dom";

import { usePermissions } from "../../contexts/usePermissions";
import { normalizeRole } from "../../shared/helpers/roleHelper";

function RoleRoute({ allowedRoles = [], children }) {
  const { rol, isLoading, isError, permissionsLoaded } = usePermissions();

  if (isLoading || (!permissionsLoaded && !isError)) {
    return <div className="py-10 text-center text-sm text-zinc-400">Cargando permisos...</div>;
  }

  if (isError) {
    return <div className="py-10 text-center text-sm text-rose-300">No se pudieron cargar los permisos.</div>;
  }

  if (!allowedRoles.map(normalizeRole).includes(normalizeRole(rol))) {
    return <Navigate to="/" replace />;
  }

  return children;
}

export default RoleRoute;
