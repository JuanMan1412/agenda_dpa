import { Link } from 'react-router-dom';
import EstadoExpediente from './EstadoExpediente';
import { fecha, origen } from '../shared/helpers/expedientes';

function TextoCelda({ value }) {
  if (!value) return <span className="missing-value" aria-label="Sin dato">—</span>;
  return <span className="cell-truncate" title={value}>{value}</span>;
}

export default function AgendaTable({ registros, puedeRegistrar = false, puedeEditar = false, registrandoId = null, onEditar, onRegistrar }) {
  return <div className="table-scroll"><table className="records-table">
    <thead><tr><th>Número de expediente</th><th>Fecha</th><th>Origen</th><th>Causante</th><th>Asunto</th><th>Estado SIGEDoc</th><th><span className="sr-only">Acciones</span></th></tr></thead>
    <tbody>{registros.map((row) => {
      const canRegister = puedeRegistrar && !row.anulado && row.estado_sigedoc === 'PENDIENTE' && (row.acciones_disponibles?.registrar_sigedoc ?? true);
      const canEdit = !row.anulado && (row.acciones_disponibles?.editar ?? puedeEditar);
      return <tr key={row.id}>
        <td><Link className="record-number" to={`/expedientes/${row.id}`}>{row.numero_formateado || `${row.numero}/${row.anio}`}</Link></td>
        <td className="date-cell">{fecha(row.fecha_hora || row.fecha_registro)}</td>
        <td><span className="origin-label">{origen(row.origen)}</span></td>
        <td className="text-cell"><TextoCelda value={row.causante} /></td>
        <td className="text-cell subject-cell"><TextoCelda value={row.asunto} /></td>
        <td><EstadoExpediente registro={row} /></td>
        <td><div className="record-actions">
          <Link className="table-action" to={`/expedientes/${row.id}`} aria-label={`Ver expediente ${row.numero_formateado}`} title="Ver expediente">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" /><circle cx="12" cy="12" r="3" /></svg><span>Ver</span>
          </Link>
          {canRegister && <button type="button" className="table-action action-primary" aria-label={`Registrar ${row.numero_formateado} en SIGEDoc`} title="Registrar en SIGEDoc" disabled={registrandoId === row.id} onClick={() => onRegistrar(row)}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><rect x="5" y="4" width="14" height="17" rx="2" /><path d="M9 4V2h6v2M9 12l2 2 4-4" /></svg><span>{registrandoId === row.id ? 'Registrando…' : 'Registrar'}</span>
          </button>}
          {canEdit && <button type="button" className="table-action" aria-label={`Editar ${row.numero_formateado}`} title="Editar expediente" onClick={() => onEditar(row)}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="m16 3 5 5-12 12-6 1 1-6L16 3ZM13 6l5 5" /></svg><span>Editar</span>
          </button>}
        </div></td>
      </tr>;
    })}</tbody>
  </table>{!registros.length && <div className="empty-state"><strong>No se encontraron expedientes.</strong><p>Probá ajustar la búsqueda o limpiar los filtros.</p></div>}</div>;
}
