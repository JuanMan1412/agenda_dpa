import { useEffect, useState } from "react";
import { listarAgenda } from "./api/agenda";
import AgendaForm from "./components/AgendaForm";
import AgendaTable from "./components/AgendaTable";

export default function App() {
  const [registros, setRegistros] = useState([]);

  useEffect(() => {
    listarAgenda().then(setRegistros).catch(console.error);
  }, []);

  function handleRegistroCreado(nuevo) {
    setRegistros((prev) => [nuevo, ...prev]);
  }

  return (
    <div style={{ maxWidth: 700, margin: "0 auto", padding: 24 }}>
      <h1>Agenda de mesa de entradas</h1>
      <AgendaForm onRegistroCreado={handleRegistroCreado} />
      <hr />
      <AgendaTable registros={registros} />
    </div>
  );
}
