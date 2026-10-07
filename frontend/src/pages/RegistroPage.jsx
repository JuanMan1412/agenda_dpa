import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { keepPreviousData, useQuery, useQueryClient } from '@tanstack/react-query';
import { listarAgenda, listarPendientes, resumenAgenda } from '../api/agenda';
import AgendaForm from '../components/AgendaForm';
import AgendaTable from '../components/AgendaTable';
import { usePermissions } from '../contexts/usePermissions';
import { errorMessage, origen } from '../shared/helpers/expedientes';

export default function RegistroPage({ pendientes = false }) {
  const [filters, setFilters] = useState({ anio: '', q: '', estado: 'TODOS', origen: '', hoy: false, page: 1 });
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { getSectionAccess, canViewSection } = usePermissions();
  const access = getSectionAccess('agenda');
  const params = { ...filters, ...(pendientes ? { estado: 'PENDIENTE', orden: 'fecha_asc' } : {}) };
  if (!params.anio) delete params.anio;
  if (!params.origen) delete params.origen;
  const summary = useQuery({ queryKey: ['expedientes', 'resumen', filters.anio], queryFn: ({ signal }) => resumenAgenda(filters.anio, signal), refetchInterval: 10000 });
  const list = useQuery({ queryKey: ['expedientes', 'lista', pendientes, params], queryFn: ({ signal }) => (pendientes ? listarPendientes : listarAgenda)(params, signal), placeholderData: keepPreviousData, refetchInterval: 60000 });
  const numeracion = summary.data?.numeracion;
  const rows = list.data?.results || [];
  const tabs = [{ value: 'TODOS', label: 'Todos' }, { value: 'PENDIENTE', label: 'Pendientes SIGEDoc' }, { value: 'REGISTRADO', label: 'Registrados' }, { value: 'ANULADO', label: 'Anulados' }];
  function change(name, value) { setFilters((current) => ({ ...current, [name]: value, page: 1 })); }
  function created(registro) {
    toast.success(`Expediente N.º ${registro.numero_formateado} creado correctamente.`, {
      description: 'Estado SIGEDoc: pendiente.',
      action: { label: 'Ver expediente', onClick: () => navigate(`/expedientes/${registro.id}`) },
    });
    setShowForm(false);
    queryClient.invalidateQueries({ queryKey: ['expedientes'] });
  }

  return <main className="registro-page">
    <div className="page-heading"><div><p className="eyebrow">Mesa de Entrada · DPA</p>
      <h1>{pendientes ? 'Pendientes SIGEDoc' : 'Registro de Expedientes DPA'}</h1>
      <p className="muted">{pendientes ? 'Expedientes pendientes de registración, del más antiguo al más reciente.' : 'Un registro único para asignar, consultar y controlar los números de expediente.'}</p>
    </div>{access.crear_registro && <button className="primary" onClick={() => setShowForm(true)} disabled={!numeracion?.habilitado}>+ Nuevo registro</button>}</div>

    {numeracion && !numeracion.habilitado && <div className="notice warning" role="status">
      <strong>Nuevas asignaciones bloqueadas</strong>
      <p>Antes de habilitarlas se debe comparar el correlativo con el libro físico. Último en base: {numeracion.ultimo_numero_base ?? 'sin registros'}/{numeracion.anio}. Próximo propuesto: <strong>{numeracion.proximo_numero}/{numeracion.anio}</strong>.</p>
    </div>}

    {!pendientes && <div className="stats-grid">
      <article className="stat-card"><p>Último número asignado</p><strong>{summary.data?.ultimo_numero_formateado || '—'}</strong><span>Incluye registros anulados</span></article>
      <article className="stat-card"><p>Pendientes SIGEDoc</p><strong>{summary.data?.pendientes ?? '—'}</strong>{canViewSection('pendientes_sigedoc') && <Link to="/pendientes-sigedoc">Ver pendientes →</Link>}</article>
      <article className="stat-card"><p>Registrados hoy</p><strong>{summary.data?.registrados_hoy ?? '—'}</strong><span>Confirmados en SIGEDoc</span></article>
      <article className="stat-card"><p>Anulados</p><strong>{summary.data?.anulados ?? '—'}</strong><span>Conservados en el registro</span></article>
    </div>}

    <section className="records-panel" aria-label="Expedientes">
      <div className="filter-bar">
        <form className="search-form" onSubmit={(event) => { event.preventDefault(); change('q', search.trim()); }}>
          <label className="sr-only" htmlFor="buscar-expedientes">Buscar expedientes</label>
          <input id="buscar-expedientes" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Número, causante, asunto o referencia…" />
          <button type="submit" className="secondary">Buscar</button>
        </form>
        <label>Año<select aria-label="Año" value={filters.anio} onChange={(event) => change('anio', event.target.value)}><option value="">Todos los años</option>{summary.data?.anios.map((year) => <option key={year} value={year}>{year}</option>)}</select></label>
        <label>Origen<select aria-label="Origen" value={filters.origen} onChange={(event) => change('origen', event.target.value)}><option value="">Todos los orígenes</option>{summary.data?.origenes.map((value) => <option key={value} value={value}>{origen(value)}</option>)}</select></label>
        <label className="checkbox-label"><input type="checkbox" checked={filters.hoy} onChange={(event) => change('hoy', event.target.checked)} /> Hoy</label>
      </div>
      {!pendientes && <div className="filter-tabs" role="group" aria-label="Estado del expediente">{tabs.map((tab) => <button key={tab.value} className={filters.estado === tab.value ? 'active' : ''} aria-pressed={filters.estado === tab.value} onClick={() => change('estado', tab.value)}>{tab.label}</button>)}</div>}
      {summary.isError && <p role="alert">{errorMessage(summary.error, 'No se pudo cargar el resumen.')}</p>}
      {list.isError ? <div className="empty-state"><p role="alert">{errorMessage(list.error, 'No se pudo cargar el registro.')}</p><button onClick={() => list.refetch()}>Reintentar</button></div> : list.isPending ? <p className="empty-state" role="status">Cargando expedientes…</p> : <AgendaTable registros={rows} pendientes={pendientes} puedeRegistrar={access.registrar_sigedoc} puedeEditar={access.editar_registro} onEditar={setEditing} />}
      <div className="table-footer"><span>{list.data?.count ?? 0} expedientes · Página {filters.page}</span><div><button className="secondary" disabled={filters.page <= 1 || list.isFetching} onClick={() => setFilters((current) => ({ ...current, page: current.page - 1 }))}>Anterior</button><button className="secondary" disabled={!list.data?.next || list.isFetching} onClick={() => setFilters((current) => ({ ...current, page: current.page + 1 }))}>Siguiente</button></div></div>
    </section>

    {showForm && <div className="modal-backdrop"><section className="dialog" role="dialog" aria-modal="true" aria-labelledby="nuevo-registro-title"><h2 id="nuevo-registro-title">Nuevo registro</h2><AgendaForm onRegistroCreado={created} onCancel={() => setShowForm(false)} /></section></div>}
    {editing && <div className="modal-backdrop"><section className="dialog" role="dialog" aria-modal="true" aria-labelledby="editar-registro-title"><h2 id="editar-registro-title">Editar expediente {editing.numero_formateado}</h2><AgendaForm registro={editing} onCancel={() => setEditing(null)} onRegistroCreado={(data) => {
      queryClient.setQueryData(['expedientes', 'detalle', String(data.id)], data);
      queryClient.invalidateQueries({ queryKey: ['expedientes'] });
      setEditing(null);
    }} /></section></div>}
  </main>;
}
