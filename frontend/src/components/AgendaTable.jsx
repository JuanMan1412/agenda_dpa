import { Link } from 'react-router-dom';
import { useEffect, useState } from 'react';
import EstadoExpediente from './EstadoExpediente';
import { fecha, origen, tiempoPendiente } from '../shared/helpers/expedientes';

export default function AgendaTable({ registros, pendientes = false, puedeRegistrar = false }) {
  const [now, setNow] = useState(Date.now);
  useEffect(() => {
    if (!pendientes) return;
    const timer = setInterval(() => setNow(Date.now()), 60000);
    return () => clearInterval(timer);
  }, [pendientes]);
  return <div className="table-scroll"><table className="records-table">
    <thead><tr><th>N.º / año</th><th>Fecha</th><th>Origen</th><th>Causante</th><th>Asunto</th><th>{pendientes ? 'Tiempo pendiente' : 'SIGEDoc'}</th><th><span className="sr-only">Acciones</span></th></tr></thead>
    <tbody>{registros.map((row) => <tr key={row.id}>
      <td><Link className="record-number" to={`/expedientes/${row.id}`}>{row.numero_formateado || `${row.numero}/${row.anio}`}</Link></td>
      <td className="date-cell">{fecha(row.fecha_hora || row.fecha_registro)}</td>
      <td><span className="origin-label">{origen(row.origen)}</span></td>
      <td>{row.causante || <span className="muted">Sin dato histórico</span>}</td>
      <td className="subject-cell">{row.asunto || <span className="muted">Sin dato histórico</span>}</td>
      <td>{pendientes ? tiempoPendiente(row.fecha_hora, now) : <EstadoExpediente registro={row} />}</td>
      <td><Link className="row-action" to={`/expedientes/${row.id}`}>{pendientes && puedeRegistrar ? 'Registrar →' : 'Ver →'}</Link></td>
    </tr>)}</tbody>
  </table>{!registros.length && <div className="empty-state"><strong>No hay expedientes para esta búsqueda.</strong><p>Probá con otro número, año o filtro.</p></div>}</div>;
}
