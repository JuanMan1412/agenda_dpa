import AgendaTable from "./AgendaTable";
import Icon from "./Icon";
import "./AgendaPanel.css";

export default function AgendaPanel({ registros, cargando, error, pageSize, pagina, onPageChange, estado, onEstadoChange, buscar, onBuscarChange, onMarkLoaded }) {
  return <section className="agenda-panel">
    <header className="agenda-panel__header"><div><Icon name="list" /><h2>Entradas recientes</h2></div><span>{registros.length} registros</span></header>
    <div className="agenda-panel__filters"><input value={buscar} onChange={(event) => onBuscarChange(event.target.value)} placeholder="Buscar por número, causante o asunto" aria-label="Buscar expedientes" /><div>{[["", "Todos"], ["pendiente", "Pendientes"], ["cargado", "Cargados"]].map(([valor, texto]) => <button key={valor} type="button" className={estado === valor ? "is-active" : ""} onClick={() => onEstadoChange(valor)}>{texto}</button>)}</div></div>
    {error ? <p className="agenda-panel__message agenda-panel__message--error">No fue posible cargar los registros. Verificá que el backend esté disponible.</p> : cargando ? <p className="agenda-panel__message">Cargando agenda...</p> : <AgendaTable registros={registros} pageSize={pageSize} pagina={pagina} onPageChange={onPageChange} onMarkLoaded={onMarkLoaded} />}
  </section>;
}
