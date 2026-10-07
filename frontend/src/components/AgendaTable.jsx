import { Link } from 'react-router-dom';
import { useEffect, useState } from 'react';
import EstadoExpediente from './EstadoExpediente';
import { fecha, origen, tiempoPendiente } from '../shared/helpers/expedientes';

export default function AgendaTable({ registros, pendientes = false, puedeRegistrar = false, puedeEditar = false, onEditar }) {
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
      <td><div className="record-actions"><Link className="table-action" to={`/expedientes/${row.id}`} title={pendientes && puedeRegistrar ? 'Registrar en SIGEDoc' : 'Ver expediente'}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          {pendientes && puedeRegistrar ? <><rect x="5" y="4" width="14" height="17" rx="2" /><path d="M9 4V2h6v2M9 12l2 2 4-4" /></> : <><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" /><circle cx="12" cy="12" r="3" /></>}
        </svg><span>{pendientes && puedeRegistrar ? 'Registrar' : 'Ver'}</span></Link>
        {!row.anulado && (row.acciones_disponibles?.editar ?? puedeEditar) && <button type="button" className="table-action" title="Editar expediente" onClick={() => onEditar(row)}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="m16 3 5 5-12 12-6 1 1-6L16 3ZM13 6l5 5" /></svg><span>Editar</span>
        </button>}
      </div></td>
    </tr>)}</tbody>
  </table>{!registros.length && <div className="empty-state"><strong>No hay expedientes para esta búsqueda.</strong><p>Probá con otro número, año o filtro.</p></div>}</div>;
}
