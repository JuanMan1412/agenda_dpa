export default function EstadoExpediente({ registro }) {
  const cancelled = registro.anulado;
  const done = registro.estado_sigedoc === 'REGISTRADO';
  return <span className={`status-badge ${cancelled ? 'cancelled' : done ? 'registered' : 'pending'}`}>
    <span aria-hidden="true">●</span> {cancelled ? 'Anulado' : done ? 'Registrado' : 'Pendiente'}
  </span>;
}
