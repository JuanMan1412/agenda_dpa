import { useRef, useState } from 'react';
import { toast } from 'sonner';
import { keepPreviousData, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { errorMessage } from '../shared/helpers/expedientes';

const roles = ['ADMINISTRADOR', 'ADMINISTRATIVO', 'CONSULTOR'];

export default function UsuariosPage() {
  const [filters, setFilters] = useState({ q: '', rol: '', is_active: '', page: 1 });
  const [search, setSearch] = useState('');
  const [dialog, setDialog] = useState(null);
  const [busy, setBusy] = useState(false);
  const pending = useRef(false);
  const queryClient = useQueryClient();
  const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value !== ''));
  const list = useQuery({ queryKey: ['usuarios', params], queryFn: async ({ signal }) => (await api.get('usuarios/', { params, signal })).data, placeholderData: keepPreviousData });
  function change(name, value) { setFilters((old) => ({ ...old, page: 1, [name]: value })); }
  function open(type, user) { setDialog({ type, user }); }
  async function save(event) {
    event.preventDefault();
    if (pending.current) return;
    pending.current = true;
    setBusy(true);
    try {
      const { type, user } = dialog;
      const endpoint = `usuarios/${user?.id ? `${user.id}/` : ''}`;
      if (type === 'eliminar') await api.delete(endpoint);
      else if (type === 'estado') await api.patch(endpoint, { is_active: !user.is_active });
      else {
        const form = new FormData(event.currentTarget);
        const payload = { rol: form.get('rol'), is_active: form.get('is_active') === 'true', email: form.get('email') };
        if (!user) for (const field of ['username', 'nombre', 'apellido']) payload[field] = form.get(field);
        if (user) await api.patch(endpoint, payload); else await api.post(endpoint, payload);
      }
      await queryClient.invalidateQueries({ queryKey: ['usuarios'] });
      await queryClient.invalidateQueries({ queryKey: ['me', 'permisos'] });
      toast.success(type === 'eliminar' ? 'Usuario eliminado.' : type === 'estado'
        ? user.is_active ? 'Usuario desactivado.' : 'Usuario activado.'
        : user ? 'Usuario actualizado.' : 'Usuario creado.');
      setDialog(null);
    } catch (requestError) { toast.error(errorMessage(requestError)); }
    finally { pending.current = false; setBusy(false); }
  }
  const editing = dialog && ['nuevo', 'editar'].includes(dialog.type);
  return <main className="registro-page">
    <div className="page-heading"><div><p className="eyebrow">Administración</p><h1>Usuarios</h1><p className="muted">Administrá los usuarios y permisos de acceso al Registro de Expedientes DPA.</p></div><button className="primary" onClick={() => open('nuevo')}>+ Nuevo usuario</button></div>
    <p className="notice">El ingreso y la identidad se administran en Portal DPA. El alta prepara el acceso local para un usuario existente del Portal; no crea una cuenta central ni una contraseña.</p>
    <section className="records-panel" aria-label="Usuarios">
      <div className="filter-bar"><form className="search-form" onSubmit={(event) => { event.preventDefault(); change('q', search.trim()); }}><input aria-label="Buscar usuarios" placeholder="Nombre o usuario" value={search} onChange={(event) => setSearch(event.target.value)} /><button className="secondary">Buscar</button></form>
        <label>Rol<select value={filters.rol} onChange={(event) => change('rol', event.target.value)}><option value="">Todos los roles</option>{roles.map((role) => <option key={role}>{role}</option>)}</select></label>
        <label>Estado<select value={filters.is_active} onChange={(event) => change('is_active', event.target.value)}><option value="">Todos los estados</option><option value="true">Activo</option><option value="false">Inactivo</option></select></label>
      </div>
      {list.isPending ? <p role="status" className="empty-state">Cargando usuarios…</p> : list.isError ? <div className="empty-state"><p role="alert">{errorMessage(list.error)}</p><button onClick={() => list.refetch()}>Reintentar</button></div> : <div className="table-scroll"><table className="records-table"><thead><tr><th>Nombre</th><th>Usuario</th><th>Rol</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>{list.data.results.map((user) => <tr key={user.id}><td>{user.nombre_visible}</td><td>{user.username}</td><td>{user.rol || 'Sin rol'}</td><td>{user.is_active ? 'Activo' : 'Inactivo'}</td><td><button className="secondary" onClick={() => open('editar', user)}>Editar</button> <button className="secondary" onClick={() => open('estado', user)}>{user.is_active ? 'Desactivar' : 'Activar'}</button> <button className="danger-link" onClick={() => open('eliminar', user)}>Eliminar</button></td></tr>)}</tbody></table>{list.data.count === 0 && <p className="empty-state">No se encontraron usuarios.</p>}</div>}
      <div className="table-footer"><span>{list.isPending ? 'Cargando…' : `${list.data?.count ?? 0} usuarios · Página ${filters.page}`}</span><div><button className="secondary" disabled={filters.page <= 1 || list.isFetching} onClick={() => change('page', filters.page - 1)}>Anterior</button><button className="secondary" disabled={!list.data?.next || list.isFetching} onClick={() => setFilters((old) => ({ ...old, page: old.page + 1 }))}>Siguiente</button></div></div>
    </section>
    {dialog && <div className="modal-backdrop"><section className="dialog" role="dialog" aria-modal="true" aria-labelledby="usuario-dialog-title"><h2 id="usuario-dialog-title">{editing ? dialog.user ? 'Editar usuario' : 'Nuevo usuario' : dialog.type === 'eliminar' ? 'Eliminar usuario' : dialog.user.is_active ? 'Desactivar usuario' : 'Activar usuario'}</h2>
      <form className="record-form" onSubmit={save}>{editing ? <>
        {dialog.user ? <p>{dialog.user.nombre_visible} · {dialog.user.username}<br />La identidad se actualiza desde Portal DPA.</p> : <><label>Usuario de Portal DPA<input name="username" maxLength={255} required autoFocus /></label><label>Nombre<input name="nombre" maxLength={150} /></label><label>Apellido<input name="apellido" maxLength={150} /></label></>}
        <label>Email local<input type="email" name="email" maxLength={254} defaultValue={dialog.user?.email || ''} /></label>
        <label>Rol<select aria-label="Rol" name="rol" defaultValue={dialog.user?.rol || 'CONSULTOR'}>{roles.map((role) => <option key={role}>{role}</option>)}</select></label>
        <label>Estado<select aria-label="Estado" name="is_active" defaultValue={String(dialog.user?.is_active ?? true)}><option value="true">Activo</option><option value="false">Inactivo</option></select></label>
      </> : <p>{dialog.type === 'eliminar' ? `¿Eliminar definitivamente a ${dialog.user.nombre_visible}? Sólo se permite si no posee actividad histórica.` : dialog.user.is_active ? `¿Desactivar a ${dialog.user.nombre_visible}? Ya no podrá ingresar. Sus registros históricos permanecerán asociados a su cuenta.` : `¿Activar a ${dialog.user.nombre_visible}?`}</p>}
        <div className="dialog-actions"><button type="button" className="secondary" disabled={busy} onClick={() => setDialog(null)}>Cancelar</button><button className={editing ? 'primary' : 'danger'} disabled={busy}>{busy ? 'Guardando…' : editing ? 'Guardar cambios' : 'Confirmar'}</button></div>
      </form>
    </section></div>}
  </main>;
}
