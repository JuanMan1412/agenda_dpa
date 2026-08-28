import { useState } from "react";
import { cargarManual } from "../api/agenda";

export default function AgendaForm({ onRegistroCreado }) {
  const [letra, setLetra] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!letra.trim()) return;

    setEnviando(true);
    setError(null);
    try {
      const registro = await cargarManual(letra.trim().toUpperCase());
      onRegistroCreado(registro);
      setLetra("");
    } catch (err) {
      setError("No se pudo registrar. Probá de nuevo.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <label>
        Letra
        <input
          type="text"
          value={letra}
          onChange={(e) => setLetra(e.target.value)}
          maxLength={10}
          placeholder="Ej: AP"
          required
        />
      </label>
      <button type="submit" disabled={enviando}>
        {enviando ? "Registrando..." : "Registrar"}
      </button>
      {error && <p style={{ color: "red" }}>{error}</p>}
      <p style={{ fontSize: "0.85em", color: "#666" }}>
        El número correlativo lo asigna el sistema automáticamente.
      </p>
    </form>
  );
}
