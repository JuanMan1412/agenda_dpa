import Button from "./Button";
import "./AgendaTable.css";

function formatDate(value) { return new Date(value).toLocaleString("es-AR", { dateStyle: "short", timeStyle: "short" }); }

export default function AgendaTable({ registros, pageSize, pagina, onPageChange, onMarkLoaded }) {
  const totalPaginas = Math.max(1, Math.ceil(registros.length / pageSize));
  const paginaActual = Math.min(pagina, totalPaginas);
  const inicio = (paginaActual - 1) * pageSize;
  const visibles = registros.slice(inicio, inicio + pageSize);
  return <><div className="agenda-table__scroll"><table className="agenda-table"><thead><tr><th>Número</th><th>Fecha</th><th>Letra</th><th>Causante</th><th>Asunto</th><th>Estado</th><th>Acción</th></tr></thead><tbody>{visibles.length ? visibles.map((registro) => <tr key={registro.id}><td className="agenda-table__sequence">{registro.numero}/{registro.anio}</td><td className="agenda-table__date">{formatDate(registro.fecha_hora)}</td><td>{registro.letra}</td><td>{registro.causante || "-"}</td><td className="agenda-table__subject">{registro.asunto || "-"}</td><td><span className={`status-badge status-badge--${registro.estado}`}>{registro.estado}</span></td><td>{registro.estado === "pendiente" ? <Button type="button" className="agenda-table__action" onClick={() => onMarkLoaded(registro)}>Marcar cargado</Button> : <span className="agenda-table__loaded">Cargado</span>}</td></tr>) : <tr><td className="agenda-table__empty" colSpan="7">Todavía no hay expedientes registrados.</td></tr>}</tbody></table></div><nav className="agenda-pagination" aria-label="Paginación de expedientes"><span>Mostrando {registros.length ? inicio + 1 : 0}-{Math.min(inicio + pageSize, registros.length)} de {registros.length}</span><div><button type="button" onClick={() => onPageChange(paginaActual - 1)} disabled={paginaActual === 1}>Anterior</button>{Array.from({ length: totalPaginas }, (_, index) => index + 1).map((numero) => <button key={numero} type="button" className={numero === paginaActual ? "is-active" : ""} onClick={() => onPageChange(numero)}>{numero}</button>)}<button type="button" onClick={() => onPageChange(paginaActual + 1)} disabled={paginaActual === totalPaginas}>Siguiente</button></div></nav></>;
}
