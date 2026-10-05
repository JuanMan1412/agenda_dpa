import { useRef, useState } from 'react';
import { cargarManual } from '../api/agenda';
import { errorMessage, fecha } from '../shared/helpers/expedientes';

export default function AgendaForm({ onRegistroCreado, onCancel }) {
  const [data, setData] = useState({ causante: '', asunto: '', tipo: '' });
  const [idempotencia] = useState(() => crypto.randomUUID());
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState('');
  const pending = useRef(false);
  function update(event) { setData((current) => ({ ...current, [event.target.name]: event.target.value })); }
  async function submit(event) {
    event.preventDefault();
    if (pending.current) return;
    pending.current = true;
    setEnviando(true);
    setError('');
    try {
      const registro = await cargarManual(data, idempotencia);
      onRegistroCreado(registro);
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      pending.current = false;
      setEnviando(false);
    }
  }
  return <form className="record-form" onSubmit={submit}>
    <label>Causante *<input name="causante" value={data.causante} onChange={update} maxLength={255} required autoFocus placeholder="Persona, entidad u organismo" /></label>
    <label>Asunto *<textarea name="asunto" value={data.asunto} onChange={update} maxLength={5000} required rows={4} placeholder="Descripción de la presentación" /></label>
    <label>Tipo / categoría<input name="tipo" value={data.tipo} onChange={update} maxLength={100} placeholder="Ej.: Línea de Ribera" /></label>
    <label>Fecha<input value={fecha(new Date().toISOString(), true)} readOnly /></label>
    <p className="muted">El número y el año se asignan al confirmar. El expediente quedará pendiente de registrar en SIGEDoc.</p>
    {error && <p role="alert">{error}</p>}
    <div className="dialog-actions">
      <button type="button" className="secondary" onClick={onCancel} disabled={enviando}>Cancelar</button>
      <button type="submit" className="primary" disabled={enviando}>{enviando ? 'Registrando…' : 'Registrar'}</button>
    </div>
  </form>;
}
