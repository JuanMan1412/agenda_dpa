import { usePermissions } from "../../contexts/usePermissions";
import Topbar from "../layout/Topbar";

export default function SectionRoute({ section, children }) {
  const { canViewSection, isLoading, isError, permissionsLoaded } = usePermissions();
  if (isError) return <><Topbar /><p role="alert">No se pudieron cargar los permisos. Volvé a intentar.</p></>;
  if (isLoading || !permissionsLoaded) return <p role="status">Cargando permisos...</p>;
  if (!canViewSection(section)) return <><Topbar /><p role="alert">Acceso denegado a esta sección.</p></>;
  return children;
}
