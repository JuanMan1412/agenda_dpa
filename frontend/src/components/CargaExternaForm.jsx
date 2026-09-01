import { useState } from "react";
import { marcarComoCargado } from "../api/agenda";
import Button from "./Button";
import "./AgendaForm.css";

export default function CargaExternaForm({ registro, onSuccess, onCancel }) {
  const [referencia, setReferencia] = useState(registro.referencia_externa ?? "");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(event) {
    event.preventDefault(); setEnviando(true); setError(null);
    try { await marcarComoCargado(registro.id, referencia.trim()); onSuccess(); }
    catch { setError("No se pudo actualizar el expediente. Intentá nuevamente."); }
    finally { setEnviando(false); }
  }

  return <form className="agenda-form" onSubmit={handleSubmit}>
    <p className="agenda-form__note">Se registrará la fecha y hora de carga para el expediente {registro.numero}/{registro.anio}.</p>
    <label>Referencia externa (opcional)<input value={referencia} onChange={(event) => setReferencia(event.target.value)} maxLength={100} placeholder="Número o código del sistema externo" autoFocus /></label>
    {error && <p className="agenda-form__error">{error}</p>}
    <div className="agenda-form__actions"><Button type="button" variant="secondary" onClick={onCancel}>Cancelar</Button><Button type="submit" disabled={enviando}>{enviando ? "Guardando..." : "Confirmar carga"}</Button></div>
  </form>;
}
