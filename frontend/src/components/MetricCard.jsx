import Icon from "./Icon";
import "./MetricCard.css";

export default function MetricCard({ icon, label, children }) {
  return <article className="metric-card"><div className="metric-card__top"><span>{label}</span><span className="metric-card__icon"><Icon name={icon} /></span></div>{children}</article>;
}
