import { useRef, useState } from 'react';
import { toast } from 'sonner';
import { Link, useParams } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { anularExpediente, detalleAgenda, marcarSigedoc } from '../api/agenda';
import EstadoExpediente from '../components/EstadoExpediente';
import { usePermissions } from '../contexts/usePermissions';
import { errorMessage, fecha, origen } from '../shared/helpers/expedientes';

const actions = { CREAR_REGISTRO: 'Expediente generado', EDITAR_REGISTRO: 'Datos del expediente editados', REGISTRAR_SIGEDOC: 'Registrado en SIGEDoc', ANULAR_REGISTRO: 'Expediente anulado', MIGRAR_HISTORICO: 'Registro histórico conservado' };

export default function ExpedienteDetail() {
  const { id } = useParams();
  const queryClient = useQueryClient();
  const { getSectionAccess } = usePermissions();
  const sectionAccess = getSectionAccess('agenda');
  const detail = useQuery({ queryKey: ['expedientes', 'detalle', id], queryFn: ({ signal }) => detalleAgenda(id, signal) });
  const [action, setAction] = useState('');
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const pending = useRef(false);

  async function confirm(event) {
    event.preventDefault();
    if (pending.current) return;
    pending.current = true;
    setBusy(true);
    try {
      const data = action === 'sigedoc' ? await marcarSigedoc(id) : await anularExpediente(id, reason.trim());
      queryClient.setQueryData(['expedientes', 'detalle', id], data);
      queryClient.invalidateQueries({ queryKey: ['expedientes'] });
      toast.success(action === 'sigedoc' ? 'Expediente marcado como registrado en SIGEDoc.' : 'Expediente anulado.');
      setAction('');
      setReason('');
    } catch (requestError) { toast.error(errorMessage(requestError)); }
    finally { pending.current = false; setBusy(false); }
  }
  if (detail.isPending) return <main className="registro-page"><p role="status">Cargando expediente…</p></main>;
  if (detail.isError) return <main className="registro-page"><Link to="/">← Volver al registro</Link><p role="alert">{errorMessage(detail.error, 'No se pudo cargar el expediente.')}</p><button onClick={() => detail.refetch()}>Reintentar</button></main>;
  const row = detail.data;
  const capabilities = row.acciones_disponibles;
  const access = capabilities ? { registrar_sigedoc: capabilities.registrar_sigedoc, anular_registro: capabilities.anular, editar_registro: capabilities.editar } : sectionAccess;
  return <main className="registro-page detail-page">
    <Link className="back-link" to="/">← Volver al registro</Link>
    <div className="page-heading"><div><p className="eyebrow">Registro de Expedientes DPA</p><h1>Expediente N.º {row.numero_formateado}</h1></div><EstadoExpediente registro={row} /></div>
    <div className="detail-grid"><section className="detail-card"><h2>Datos del registro</h2><dl>
      <div><dt>Origen</dt><dd>{origen(row.origen)}</dd></div><div><dt>Fecha de registro</dt><dd>{fecha(row.fecha_hora)}</dd></div>
      <div><dt>Causante</dt><dd>{row.causante || 'Sin dato en el registro histórico'}</dd></div><div><dt>Asunto</dt><dd>{row.asunto || 'Sin dato en el registro histórico'}</dd></div>
      <div><dt>Tipo / categoría</dt><dd>{row.tipo || '—'}</dd></div>{row.letra && <div><dt>Letra histórica</dt><dd>{row.letra}</dd></div>}
      <div><dt>Referencia de origen</dt><dd>{row.referencia_externa || '—'}</dd></div><div><dt>Creado por</dt><dd>{row.creado_por_nombre || row.sistema_origen || 'No informado en el registro histórico'}</dd></div>
    </dl></section>
    <section className="detail-card sigedoc-card"><p className="eyebrow">Registración en SIGEDoc</p><h2>Utilizá exactamente este número</h2><p className="expediente-number">{row.numero_formateado}</p><p className="muted">El número es el mismo en ambos sistemas. La confirmación sólo actualiza su estado de registración.</p>
      {row.estado_sigedoc === 'REGISTRADO' && <div className="notice success"><strong>Registrado en SIGEDoc</strong><p>{fecha(row.fecha_registro_sigedoc)} · {row.registrado_sigedoc_por_nombre}</p></div>}
      {!row.anulado && row.estado_sigedoc === 'PENDIENTE' && access.registrar_sigedoc && <button className="primary" onClick={() => { setAction('sigedoc'); }}>✓ Marcar como registrado en SIGEDoc</button>}
      {row.anulado ? <div className="notice cancelled"><strong>Expediente anulado</strong><p>{row.motivo_anulacion}</p><p>{fecha(row.fecha_anulacion)} · {row.anulado_por_nombre}</p><p>Este número permanece reservado y no se reutilizará.</p></div> : access.anular_registro && <button className="danger-link" onClick={() => { setAction('anular'); }}>Anular registro</button>}
    </section></div>
    <section className="detail-card audit-card"><h2>Auditoría</h2><ol className="audit-list">{row.auditoria?.map((entry) => <li key={entry.id}><time>{fecha(entry.fecha_hora)}</time><div><strong>{actions[entry.accion] || entry.accion}</strong><p>{entry.usuario_nombre || entry.sistema || 'Registro histórico'}</p>{entry.motivo && <p className="muted">{entry.motivo}</p>}</div></li>)}</ol></section>
    {action && <div className="modal-backdrop"><section className="dialog" role="dialog" aria-modal="true" aria-labelledby="confirm-title"><h2 id="confirm-title">{action === 'sigedoc' ? 'Confirmar registración en SIGEDoc' : 'Anular registro'}</h2><form className="record-form" onSubmit={confirm}>
      <p>{action === 'sigedoc' ? `¿Confirmar que el expediente ${row.numero_formateado} fue registrado en SIGEDoc?` : `El expediente ${row.numero_formateado} quedará anulado. Su número no se reutilizará.`}</p>
      {action === 'anular' && <label>Motivo obligatorio<textarea value={reason} onChange={(event) => setReason(event.target.value)} required maxLength={2000} rows={4} autoFocus /></label>}
      <div className="dialog-actions"><button type="button" className="secondary" disabled={busy} onClick={() => setAction('')}>Cancelar</button><button className={action === 'anular' ? 'danger' : 'primary'} disabled={busy || (action === 'anular' && !reason.trim())}>{busy ? 'Guardando…' : 'Confirmar'}</button></div>
    </form></section></div>}
  </main>;
}
