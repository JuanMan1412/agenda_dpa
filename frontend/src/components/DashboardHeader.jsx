import Button from "./Button";
import Icon from "./Icon";
import "./DashboardHeader.css";

export default function DashboardHeader({ onCreate }) {
  return <header className="dashboard-header">
    <div>
      <p className="dashboard-header__eyebrow">Mesa de entradas</p>
      <h1>Tablero de control de expedientes</h1>
      <p className="dashboard-header__subtitle">Seguimiento de ingresos, distribución y correlativos diarios.</p>
    </div>
    <Button type="button" onClick={onCreate}><Icon name="plus" />Registrar expediente</Button>
  </header>;
}
