import { useEffect, useState } from "react";
import { listarAgenda, obtenerEstadisticas } from "./api/agenda";
import AgendaForm from "./components/AgendaForm";
import AgendaPanel from "./components/AgendaPanel";
import CargaExternaForm from "./components/CargaExternaForm";
import DashboardHeader from "./components/DashboardHeader";
import Modal from "./components/Modal";
import StatsGrid from "./components/StatsGrid";
import "./App.css";

const PAGE_SIZE = 10;

export default function App() {
  const [registros, setRegistros] = useState([]);
  const [estadisticas, setEstadisticas] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(false);
  const [modal, setModal] = useState(null);
  const [pagina, setPagina] = useState(1);
  const [estado, setEstado] = useState("");
  const [buscar, setBuscar] = useState("");

  useEffect(() => {
    let activa = true;
    Promise.all([listarAgenda({ estado, buscar }), obtenerEstadisticas()])
      .then(([agenda, resumen]) => {
        if (!activa) return;
        setRegistros(agenda.results ?? agenda);
        setEstadisticas(resumen);
        setError(false);
      })
      .catch(() => activa && setError(true))
      .finally(() => activa && setCargando(false));
    return () => { activa = false; };
  }, [estado, buscar]);

  function refrescarDatos() {
    setCargando(true);
    Promise.all([listarAgenda({ estado, buscar }), obtenerEstadisticas()])
      .then(([agenda, resumen]) => { setRegistros(agenda.results ?? agenda); setEstadisticas(resumen); setError(false); })
      .catch(() => setError(true))
      .finally(() => setCargando(false));
  }

  function handleEstadoChange(valor) { setCargando(true); setEstado(valor); setPagina(1); }
  function handleBuscarChange(valor) { setCargando(true); setBuscar(valor); setPagina(1); }
  function handleRegistroCreado() { setModal(null); refrescarDatos(); }
  function handleCargado() { setModal(null); refrescarDatos(); }

  return <main className="app-shell">
    <DashboardHeader onCreate={() => setModal({ type: "crear" })} />
    <StatsGrid estadisticas={estadisticas} />
    <AgendaPanel registros={registros} cargando={cargando} error={error} pageSize={PAGE_SIZE} pagina={pagina} onPageChange={setPagina} estado={estado} onEstadoChange={handleEstadoChange} buscar={buscar} onBuscarChange={handleBuscarChange} onMarkLoaded={(registro) => setModal({ type: "cargar", registro })} />
    {modal?.type === "crear" && <Modal title="Registrar expediente" onClose={() => setModal(null)}><AgendaForm onRegistroCreado={handleRegistroCreado} onCancel={() => setModal(null)} /></Modal>}
    {modal?.type === "cargar" && <Modal title="Marcar como cargado" onClose={() => setModal(null)}><CargaExternaForm registro={modal.registro} onSuccess={handleCargado} onCancel={() => setModal(null)} /></Modal>}
  </main>;
}
