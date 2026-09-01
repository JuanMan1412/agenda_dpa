import "./Modal.css";

export default function Modal({ title, children, onClose }) {
  return <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
    <section className="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title" onMouseDown={(event) => event.stopPropagation()}>
      <header className="modal__header"><div><p>Nueva entrada</p><h2 id="modal-title">{title}</h2></div><button className="modal__close" type="button" onClick={onClose} aria-label="Cerrar formulario">x</button></header>
      {children}
    </section>
  </div>;
}
