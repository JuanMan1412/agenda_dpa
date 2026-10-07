import { NavLink, Outlet, Route, Routes } from 'react-router-dom';
import ProtectedRoute from './components/auth/ProtectedRoute';
import SectionRoute from './components/auth/SectionRoute';
import Topbar from './components/layout/Topbar';
import ReservasNotifications from './components/ReservasNotifications';
import PortalAccess from './pages/PortalAccess';
import RegistroPage from './pages/RegistroPage';
import ExpedienteDetail from './pages/ExpedienteDetail';
import UsuariosPage from './pages/UsuariosPage';
import { usePermissions } from './contexts/usePermissions';

function RegistroLayout() {
  const { canViewSection } = usePermissions();
  return <><ReservasNotifications /><Topbar /><nav className="main-nav" aria-label="Secciones">
    <NavLink to="/" end>Registro de expedientes</NavLink>
    {canViewSection('pendientes_sigedoc') && <NavLink to="/pendientes-sigedoc">Pendientes SIGEDoc</NavLink>}
    {canViewSection('usuarios') && <NavLink to="/usuarios">Administración · Usuarios</NavLink>}
  </nav><Outlet /></>;
}
export default function App() {
  return <Routes>
    <Route path="/portal-access" element={<PortalAccess />} />
    <Route element={<ProtectedRoute />}>
      <Route element={<SectionRoute section="agenda"><RegistroLayout /></SectionRoute>}>
        <Route path="/" element={<RegistroPage key="registro" />} />
        <Route path="/pendientes-sigedoc" element={<SectionRoute section="pendientes_sigedoc"><RegistroPage key="pendientes" pendientes /></SectionRoute>} />
        <Route path="/usuarios" element={<SectionRoute section="usuarios"><UsuariosPage /></SectionRoute>} />
        <Route path="/expedientes/:id" element={<ExpedienteDetail />} />
        <Route path="*" element={<main className="registro-page"><h1>Página no encontrada</h1></main>} />
      </Route>
    </Route>
  </Routes>;
}
