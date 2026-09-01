import MetricCard from "./MetricCard";
import "./StatsGrid.css";

function formatDuration(seconds) {
  if (seconds === null || seconds === undefined) return "Sin datos";
  const minutes = Math.round(seconds / 60);
  return minutes < 60 ? `${minutes} min` : `${Math.floor(minutes / 60)} h ${minutes % 60} min`;
}

export default function StatsGrid({ estadisticas }) {
  const datos = estadisticas ?? { pendientes: "-", cargados_hoy: "-", tiempo_promedio_segundos: null };
  return <section className="stats-grid" aria-label="Resumen de carga externa">
    <MetricCard icon="inbox" label="Pendientes de carga"><strong className="metric-card__number">{datos.pendientes}</strong><span className="metric-card__hint">expedientes por cargar</span></MetricCard>
    <MetricCard icon="split" label="Cargados hoy"><strong className="metric-card__number">{datos.cargados_hoy}</strong><span className="metric-card__hint">cargados al sistema externo</span></MetricCard>
    <MetricCard icon="hash" label="Promedio de carga hoy"><strong className="metric-card__sequence">{formatDuration(datos.tiempo_promedio_segundos)}</strong><span className="metric-card__hint">desde el ingreso hasta la carga</span></MetricCard>
  </section>;
}
