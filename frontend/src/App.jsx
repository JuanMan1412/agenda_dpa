import { NavLink, Outlet, Route, Routes } from 'react-router-dom';
import ProtectedRoute from './components/auth/ProtectedRoute';
import SectionRoute from './components/auth/SectionRoute';
import Topbar from './components/layout/Topbar';
import PortalAccess from './pages/PortalAccess';
import RegistroPage from './pages/RegistroPage';
import ExpedienteDetail from './pages/ExpedienteDetail';

function RegistroLayout() {
  return <><Topbar /><nav className="main-nav" aria-label="Secciones">
    <NavLink to="/" end>Registro de expedientes</NavLink>
    <NavLink to="/pendientes-sigedoc">Pendientes SIGEDoc</NavLink>
  </nav><Outlet /></>;
}
export default function App() {
  return <Routes>
    <Route path="/portal-access" element={<PortalAccess />} />
    <Route element={<ProtectedRoute />}>
      <Route element={<SectionRoute section="agenda"><RegistroLayout /></SectionRoute>}>
        <Route path="/" element={<RegistroPage key="registro" />} />
        <Route path="/pendientes-sigedoc" element={<RegistroPage key="pendientes" pendientes />} />
        <Route path="/expedientes/:id" element={<ExpedienteDetail />} />
        <Route path="*" element={<main className="registro-page"><h1>Página no encontrada</h1></main>} />
      </Route>
    </Route>
  </Routes>;
}
