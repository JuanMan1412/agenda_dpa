export default function AgendaTable({ registros }) {
  return (
    <table border="1" cellPadding="6" style={{ borderCollapse: "collapse", width: "100%" }}>
      <thead>
        <tr>
          <th>Número</th>
          <th>Letra</th>
          <th>Origen</th>
          <th>Fecha y hora</th>
        </tr>
      </thead>
      <tbody>
        {registros.map((r) => (
          <tr key={r.id}>
            <td>{String(r.numero).padStart(4, "0")}</td>
            <td>{r.letra}</td>
            <td>{r.origen}</td>
            <td>{new Date(r.fecha_hora).toLocaleString("es-AR")}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
