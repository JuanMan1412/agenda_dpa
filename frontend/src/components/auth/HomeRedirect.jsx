import { Navigate } from "react-router-dom";
import { usePermissions } from "../../contexts/usePermissions";

export default function HomeRedirect() {
  const { canViewSection, isLoading, isError, permissionsLoaded } = usePermissions();
  if (isError) return <p role="alert">No se pudieron cargar los permisos.</p>;
  if (isLoading || !permissionsLoaded) return <p>Cargando permisos...</p>;
  return canViewSection("agenda") ? <Navigate to="/" replace /> : <p>El usuario no tiene acceso a la agenda.</p>;
}
