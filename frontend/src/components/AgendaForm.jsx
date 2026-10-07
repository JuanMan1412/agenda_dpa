import { useRef, useState } from 'react';
import { toast } from 'sonner';
import { cargarManual, editarExpediente } from '../api/agenda';
import { errorMessage, fecha } from '../shared/helpers/expedientes';

export default function AgendaForm({ onRegistroCreado, onCancel, registro }) {
  const [data, setData] = useState({ causante: registro?.causante || '', asunto: registro?.asunto || '', tipo: registro?.tipo || '' });
  const [idempotencia] = useState(() => crypto.randomUUID());
  const [enviando, setEnviando] = useState(false);
  const pending = useRef(false);
  function update(event) { setData((current) => ({ ...current, [event.target.name]: event.target.value })); }
  async function submit(event) {
    event.preventDefault();
    if (pending.current) return;
    pending.current = true;
    setEnviando(true);
    try {
      const result = registro ? await editarExpediente(registro.id, data) : await cargarManual(data, idempotencia);
      if (registro) toast.success('Datos del expediente actualizados.');
      onRegistroCreado(result);
    } catch (requestError) {
      toast.error(errorMessage(requestError));
    } finally {
      pending.current = false;
      setEnviando(false);
    }
  }
  return <form className="record-form" onSubmit={submit}>
    <label>Causante *<input name="causante" value={data.causante} onChange={update} maxLength={255} required autoFocus placeholder="Persona, entidad u organismo" /></label>
    <label>Asunto *<textarea name="asunto" value={data.asunto} onChange={update} maxLength={5000} required rows={4} placeholder="Descripción de la presentación" /></label>
    <label>Tipo / categoría<input name="tipo" value={data.tipo} onChange={update} maxLength={100} placeholder="Ej.: Línea de Ribera" /></label>
    <label>Fecha<input value={fecha(registro?.fecha_hora || new Date().toISOString(), true)} readOnly /></label>
    <p className="muted">{registro ? 'La numeración, el origen y el estado SIGEDoc se conservan.' : 'El número y el año se asignan al confirmar. El expediente quedará pendiente de registrar en SIGEDoc.'}</p>
    <div className="dialog-actions">
      <button type="button" className="secondary" onClick={onCancel} disabled={enviando}>Cancelar</button>
      <button type="submit" className="primary" disabled={enviando}>{enviando ? 'Guardando…' : registro ? 'Guardar cambios' : 'Registrar'}</button>
    </div>
  </form>;
}
