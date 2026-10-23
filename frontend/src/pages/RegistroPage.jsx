import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { listarAgenda, marcarSigedoc, resumenAgenda } from '../api/agenda';
import AgendaForm from '../components/AgendaForm';
import AgendaTable from '../components/AgendaTable';
import { usePermissions } from '../contexts/usePermissions';
import { errorMessage, origen } from '../shared/helpers/expedientes';

const initialFilters = { anio: '', q: '', estado: 'TODOS', origen: '', hoy: false, page: 1, page_size: 10 };
const tabs = [
  { value: 'TODOS', label: 'Todos' },
  { value: 'PENDIENTE', label: 'Pendientes SIGEDoc' },
  { value: 'REGISTRADO', label: 'Registrados' },
  { value: 'ANULADO', label: 'Anulados' },
];

export default function RegistroPage() {
  const [filters, setFilters] = useState(initialFilters);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [registering, setRegistering] = useState(null);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { getSectionAccess } = usePermissions();
  const access = getSectionAccess('agenda');
  const params = { ...filters };
  if (!params.anio) delete params.anio;
  if (!params.origen) delete params.origen;
  const summary = useQuery({ queryKey: ['expedientes', 'resumen', filters.anio], queryFn: ({ signal }) => resumenAgenda(filters.anio, signal), refetchInterval: 10000 });
  const list = useQuery({ queryKey: ['expedientes', 'lista', params], queryFn: ({ signal }) => listarAgenda(params, signal), placeholderData: keepPreviousData, refetchInterval: 60000 });
  const registerMutation = useMutation({
    mutationFn: (registro) => marcarSigedoc(registro.id),
    onSuccess: (data) => {
      queryClient.setQueryData(['expedientes', 'detalle', String(data.id)], data);
      queryClient.invalidateQueries({ queryKey: ['expedientes'] });
      toast.success(`Expediente ${data.numero_formateado} registrado en SIGEDoc.`);
      setRegistering(null);
    },
    onError: (requestError) => toast.error(errorMessage(requestError, 'No se pudo registrar el expediente en SIGEDoc.')),
  });
  const numeracion = summary.data?.numeracion;
  const rows = list.data?.results || [];
  const totalPages = Math.max(1, Math.ceil((list.data?.count || 0) / filters.page_size));
  const hasActiveFilters = Boolean(search || filters.q || filters.anio || filters.origen || filters.hoy || filters.estado !== 'TODOS');

  useEffect(() => {
    const q = search.trim();
    const timer = window.setTimeout(() => setFilters((current) => current.q === q ? current : { ...current, q, page: 1 }), 300);
    return () => window.clearTimeout(timer);
  }, [search]);

  useEffect(() => {
    if (!showForm && !editing && !registering) return undefined;
    function closeOnEscape(event) {
      if (event.key === 'Escape' && !registerMutation.isPending) {
        setShowForm(false);
        setEditing(null);
        setRegistering(null);
      }
    }
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [showForm, editing, registering, registerMutation.isPending]);

  function change(name, value) { setFilters((current) => ({ ...current, [name]: value, page: 1 })); }
  function clearFilters() {
    setSearch('');
    setFilters((current) => ({ ...initialFilters, page_size: current.page_size }));
  }
  function created(registro) {
    toast.success(`Expediente N.º ${registro.numero_formateado} creado correctamente.`, {
      description: 'Estado SIGEDoc: pendiente.',
      action: { label: 'Ver expediente', onClick: () => navigate(`/expedientes/${registro.id}`) },
    });
    setShowForm(false);
    queryClient.invalidateQueries({ queryKey: ['expedientes'] });
  }

  function confirmRegistration(event) {
    event.preventDefault();
    if (!registering || registerMutation.isPending) return;
    registerMutation.mutate(registering);
  }

  return <main className="registro-page">
    <div className="page-heading">
      <div>
        <p className="eyebrow">Mesa de Entrada · DPA</p>
        <h1>Registro de Expedientes DPA</h1>
        <p className="muted">Un registro único para asignar, consultar y controlar los números de expediente.</p>
      </div>
      {access.crear_registro && <button className="primary new-record-button" onClick={() => setShowForm(true)} disabled={!numeracion?.habilitado}>
        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 3.5v13M3.5 10h13" /></svg> Nuevo registro
      </button>}
    </div>

    {numeracion && !numeracion.habilitado && <div className="notice warning" role="status">
      <strong>Nuevas asignaciones bloqueadas</strong>
      <p>Antes de habilitarlas se debe comparar el correlativo con el libro físico. Último número registrado: {summary.data?.ultimo_numero_formateado || 'sin registros'}. Próximo propuesto: <strong>{numeracion.proximo_numero_formateado}</strong>.</p>
    </div>}

    <section className="stats-grid" aria-label="Resumen de expedientes">
      <article className="stat-card"><p>Último número asignado</p><strong>{summary.data?.ultimo_numero_formateado || '—'}</strong><span>Incluye registros anulados</span></article>
      <button type="button" className="stat-card stat-card-link" aria-label="Filtrar expedientes pendientes SIGEDoc" aria-pressed={filters.estado === 'PENDIENTE'} onClick={() => change('estado', 'PENDIENTE')}><p>Pendientes SIGEDoc</p><strong>{summary.data?.pendientes ?? '—'}</strong><span>Ver expedientes pendientes <span aria-hidden="true">→</span></span></button>
      <article className="stat-card"><p>Registrados hoy</p><strong>{summary.data?.registrados_hoy ?? '—'}</strong><span>Confirmados en SIGEDoc</span></article>
      <article className="stat-card"><p>Anulados</p><strong>{summary.data?.anulados ?? '—'}</strong><span>Conservados en el registro</span></article>
    </section>

    <section className="records-panel" aria-label="Expedientes">
      <div className="filter-bar">
        <div className="search-form">
          <label className="sr-only" htmlFor="buscar-expedientes">Buscar expedientes</label>
          <svg className="search-icon" viewBox="0 0 20 20" aria-hidden="true"><circle cx="8.8" cy="8.8" r="5.8" /><path d="m13.2 13.2 4 4" /></svg>
          <input id="buscar-expedientes" type="search" value={search} onChange={(event) => { setSearch(event.target.value); setFilters((current) => current.page === 1 ? current : { ...current, page: 1 }); }} placeholder="Expediente, letra, causante o asunto" aria-describedby="buscar-estado" />
          <span id="buscar-estado" className="search-status" role="status" aria-live="polite">{search.trim() !== filters.q || (list.isFetching && Boolean(filters.q)) ? 'Buscando…' : ''}</span>
        </div>
        <label>Año<select aria-label="Año" value={filters.anio} onChange={(event) => change('anio', event.target.value)}><option value="">Todos</option>{summary.data?.anios.map((year) => <option key={year} value={year}>{year}</option>)}</select></label>
        <label>Origen<select aria-label="Origen" value={filters.origen} onChange={(event) => change('origen', event.target.value)}><option value="">Todos</option>{summary.data?.origenes.map((value) => <option key={value} value={value}>{origen(value)}</option>)}</select></label>
        <label className="checkbox-label"><input type="checkbox" checked={filters.hoy} onChange={(event) => change('hoy', event.target.checked)} /> Hoy</label>
        {hasActiveFilters && <button type="button" className="clear-filters" onClick={clearFilters}>Limpiar filtros</button>}
      </div>

      <div className="filter-tabs" role="group" aria-label="Estado del expediente">{tabs.map((tab) => <button key={tab.value} className={filters.estado === tab.value ? 'active' : ''} aria-pressed={filters.estado === tab.value} onClick={() => change('estado', tab.value)}>{tab.label}</button>)}</div>
      {summary.isError && <p className="inline-error" role="alert">{errorMessage(summary.error, 'No se pudo cargar el resumen.')}</p>}
      {list.isError ? <div className="empty-state"><p role="alert">{errorMessage(list.error, 'No se pudo cargar el registro.')}</p><button className="secondary" onClick={() => list.refetch()}>Reintentar</button></div> : list.isPending || list.isPlaceholderData || search.trim() !== filters.q ? <p className="empty-state" role="status">{search.trim() !== filters.q ? 'Buscando expedientes…' : 'Actualizando expedientes…'}</p> : <AgendaTable registros={rows} puedeRegistrar={access.registrar_sigedoc} puedeEditar={access.editar_registro} registrandoId={registerMutation.isPending ? registerMutation.variables?.id : null} onEditar={setEditing} onRegistrar={setRegistering} />}
      <div className="table-footer">
        <div className="table-summary"><span>{list.data?.count ?? 0} expedientes</span><span>Página {Math.min(filters.page, totalPages)} de {totalPages}</span></div>
        <div className="table-controls"><label>Filas<select aria-label="Filas por página" value={filters.page_size} onChange={(event) => change('page_size', Number(event.target.value))}><option value={10}>10</option><option value={25}>25</option><option value={50}>50</option><option value={100}>100</option></select></label>
          <button className="secondary" disabled={filters.page <= 1 || list.isFetching} onClick={() => setFilters((current) => ({ ...current, page: current.page - 1 }))}>Anterior</button>
          <button className="secondary" disabled={!list.data?.next || list.isFetching} onClick={() => setFilters((current) => ({ ...current, page: current.page + 1 }))}>Siguiente</button>
        </div>
      </div>
    </section>

    {registering && <div className="modal-backdrop"><section className="dialog" role="dialog" aria-modal="true" aria-labelledby="registrar-title"><div className="dialog-heading"><div><p className="eyebrow">SIGEDoc</p><h2 id="registrar-title">Confirmar registro</h2></div><button type="button" className="icon-button" aria-label="Cerrar" disabled={registerMutation.isPending} onClick={() => setRegistering(null)}>×</button></div><form className="record-form" onSubmit={confirmRegistration}><p>¿Confirmás que el expediente <strong>{registering.numero_formateado}</strong> ya fue registrado en SIGEDoc?</p><div className="dialog-actions"><button type="button" className="secondary" disabled={registerMutation.isPending} onClick={() => setRegistering(null)}>Cancelar</button><button className="primary" disabled={registerMutation.isPending}>{registerMutation.isPending ? 'Registrando…' : 'Confirmar'}</button></div></form></section></div>}
    {showForm && <div className="modal-backdrop"><section className="dialog" role="dialog" aria-modal="true" aria-labelledby="nuevo-registro-title"><div className="dialog-heading"><div><p className="eyebrow">Mesa de Entrada · DPA</p><h2 id="nuevo-registro-title">Nuevo registro</h2></div><button type="button" className="icon-button" aria-label="Cerrar" onClick={() => setShowForm(false)}>×</button></div><AgendaForm onRegistroCreado={created} onCancel={() => setShowForm(false)} /></section></div>}
    {editing && <div className="modal-backdrop"><section className="dialog" role="dialog" aria-modal="true" aria-labelledby="editar-registro-title"><div className="dialog-heading"><div><p className="eyebrow">Registro de Expedientes DPA</p><h2 id="editar-registro-title">Editar expediente</h2><p className="muted">{editing.numero_formateado}</p></div><button type="button" className="icon-button" aria-label="Cerrar" onClick={() => setEditing(null)}>×</button></div><AgendaForm registro={editing} onCancel={() => setEditing(null)} onRegistroCreado={(data) => {
      queryClient.setQueryData(['expedientes', 'detalle', String(data.id)], data);
      queryClient.invalidateQueries({ queryKey: ['expedientes'] });
      setEditing(null);
    }} /></section></div>}
  </main>;
}
