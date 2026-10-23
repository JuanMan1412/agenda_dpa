export default function EstadoExpediente({ registro }) {
  const cancelled = registro.anulado;
  const done = registro.estado_sigedoc === 'REGISTRADO';
  const label = cancelled ? 'Anulado' : done ? 'Registrado' : 'Pendiente';
  return <span className={`status-badge ${cancelled ? 'cancelled' : done ? 'registered' : 'pending'}`}>
    <span className="status-dot" aria-hidden="true" /> {label}
  </span>;
}
