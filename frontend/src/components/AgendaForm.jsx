import { useState } from "react";
import { cargarManual } from "../api/agenda";
import Button from "./Button";
import "./AgendaForm.css";

export default function AgendaForm({ onRegistroCreado, onCancel }) {
  const [letra, setLetra] = useState("");
  const [asunto, setAsunto] = useState("");
  const [causante, setCausante] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState(null);

  function actualizarLetra(valor) {
    setLetra(valor.replace(/[^\p{L}]/gu, ""));
  }

  function actualizarCausante(valor) {
    setCausante(valor.replace(/[^\p{L}\s]/gu, ""));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setEnviando(true);
    setError(null);
    try {
      const registro = await cargarManual({ letra: letra.trim().toUpperCase(), asunto: asunto.trim(), causante: causante.trim() });
      onRegistroCreado(registro);
    } catch {
      setError("No se pudo registrar el expediente. Intentá nuevamente.");
    } finally {
      setEnviando(false);
    }
  }

  return <form className="agenda-form" onSubmit={handleSubmit}>
    <div className="agenda-form__row"><label>Letra<input type="text" value={letra} onChange={(event) => actualizarLetra(event.target.value)} maxLength={10} placeholder="Ej: AP" required autoFocus /></label><label>Causante (opcional)<input type="text" value={causante} onChange={(event) => actualizarCausante(event.target.value)} maxLength={200} placeholder="Nombre y apellido" /></label></div>
    <label>Asunto (opcional)<textarea value={asunto} onChange={(event) => setAsunto(event.target.value)} placeholder="Describí brevemente el motivo del expediente" rows="3" /></label>
    {error && <p className="agenda-form__error">{error}</p>}
    <p className="agenda-form__note">El número correlativo y la fecha se asignan automáticamente.</p>
    <div className="agenda-form__actions"><Button type="button" variant="secondary" onClick={onCancel}>Cancelar</Button><Button type="submit" disabled={enviando}>{enviando ? "Registrando..." : "Registrar expediente"}</Button></div>
  </form>;
}
