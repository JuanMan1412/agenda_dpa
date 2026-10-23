import { useRef, useState } from 'react';
import { toast } from 'sonner';
import { cargarManual, editarExpediente } from '../api/agenda';
import { errorMessage } from '../shared/helpers/expedientes';

const letraValida = /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{1,10}$/;

export default function AgendaForm({ onRegistroCreado, onCancel, registro }) {
  const [data, setData] = useState({ causante: registro?.causante || '', asunto: registro?.asunto || '', letra: registro?.letra || '' });
  const [errors, setErrors] = useState({});
  const [idempotencia] = useState(() => crypto.randomUUID());
  const [enviando, setEnviando] = useState(false);
  const pending = useRef(false);

  function update(event) {
    const { name, value } = event.target;
    setData((current) => ({ ...current, [name]: value }));
    if (name === 'letra') {
      setErrors((current) => ({
        ...current,
        letra: !value.trim() ? 'La letra es obligatoria.' : !letraValida.test(value) ? 'Ingresá únicamente letras, sin espacios ni signos.' : '',
      }));
    }
  }

  async function submit(event) {
    event.preventDefault();
    const letra = data.letra.trim();
    if (!letra) { setErrors({ letra: 'La letra es obligatoria.' }); return; }
    if (!letraValida.test(letra)) { setErrors({ letra: 'Ingresá únicamente letras, sin espacios ni signos.' }); return; }
    setErrors({});
    if (pending.current) return;
    pending.current = true;
    setEnviando(true);
    try {
      const payload = { ...data, letra };
      const result = registro ? await editarExpediente(registro.id, payload) : await cargarManual(payload, idempotencia);
      if (registro) toast.success('Datos del expediente actualizados.');
      onRegistroCreado(result);
    } catch (requestError) {
      const fieldError = requestError?.response?.data?.letra;
      if (fieldError) setErrors((current) => ({ ...current, letra: Array.isArray(fieldError) ? fieldError.join(' ') : String(fieldError) }));
      toast.error(errorMessage(requestError));
    } finally {
      pending.current = false;
      setEnviando(false);
    }
  }

  return <form className="record-form" onSubmit={submit}>
    <label>Letra *<input name="letra" value={data.letra} onChange={update} maxLength={10} aria-invalid={Boolean(errors.letra)} aria-describedby={errors.letra ? 'letra-error' : undefined} autoFocus placeholder="Ej.: A, ED" /></label>
    {errors.letra && <span id="letra-error" className="field-error" role="alert">{errors.letra}</span>}
    <label>Causante (opcional)<input name="causante" value={data.causante} onChange={update} maxLength={255} placeholder="Persona, entidad u organismo" /></label>
    <label>Asunto (opcional)<textarea name="asunto" value={data.asunto} onChange={update} maxLength={5000} rows={4} placeholder="Descripción de la presentación" /></label>
    <p className="muted">{registro ? 'La numeración, el origen y la categoría se conservan.' : 'La fecha, la categoría y el número se asignan automáticamente.'}</p>
    <div className="dialog-actions">
      <button type="button" className="secondary" onClick={onCancel} disabled={enviando}>Cancelar</button>
      <button type="submit" className="primary" disabled={enviando}>{enviando ? 'Guardando…' : registro ? 'Guardar cambios' : 'Registrar'}</button>
    </div>
  </form>;
}
