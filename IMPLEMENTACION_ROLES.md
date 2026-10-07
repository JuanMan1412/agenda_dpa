# Roles, permisos y administración de usuarios

Se reutilizan `usuarios.User`, `roles.Rol`, la matriz de `roles/permissions.py`, el ingreso de Portal DPA y las rutas actuales de Registro de Expedientes. Mesa de Entrada sigue siendo una oficina/origen.

## Permisos

| Función | ADMINISTRADOR | ADMINISTRATIVO | CONSULTOR |
| --- | --- | --- | --- |
| Listar, buscar, filtrar y consultar expedientes | Sí | Sí | Sí |
| Crear y editar datos descriptivos | Sí | Sí | No |
| Acceder a Pendientes y registrar SIGEDoc | Sí | Sí | No |
| Anular | Sí | No | No |
| Administrar usuarios | Sí | No | No |

La anulación ya estaba reservada al ADMINISTRADOR; se conserva esa regla. No se agregan roles ni se usa `is_superuser` para eludir la matriz de la API. Un rol inexistente, deshabilitado o una cuenta inactiva no obtiene acceso.

DRF valida cada operación. React recibe secciones desde `/api/me/permisos/` y capacidades por expediente en `acciones_disponibles`. Oculta enlaces/botones y protege rutas directas. Los filtros de estado del registro general siguen disponibles para consulta; la bandeja operativa de Pendientes tiene su propio permiso y endpoint.

## Endpoints

| Endpoint | Métodos | Acceso |
| --- | --- | --- |
| `/api/usuarios/` | GET, POST | ADMINISTRADOR |
| `/api/usuarios/{id}/` | GET, PATCH, PUT, DELETE | ADMINISTRADOR |
| `/api/expedientes/pendientes-sigedoc/` | GET | ADMINISTRADOR, ADMINISTRATIVO |
| `/api/expedientes/` | GET; nuevo POST | Consulta: todos; creación: ADMINISTRADOR, ADMINISTRATIVO |
| `/api/expedientes/{id}/` | GET; nuevos PATCH y PUT | Consulta: todos; edición: ADMINISTRADOR, ADMINISTRATIVO |

Se conservan `/api/expedientes/manual/`, `/api/agenda/manual/`, las acciones `registrar-sigedoc/` y `anular/`, y las rutas de integración con credenciales de servicio.

Usuarios usa paginación de 25 filas (máximo 100) y filtros `q`, `rol`, `is_active=true|false`, `page`, `page_size`. Activación/desactivación se realiza mediante PATCH con `is_active`; no hace falta otro endpoint.

## Identidad de Portal DPA

El alta prepara una cuenta local por el username del Portal con contraseña inutilizable. No crea identidad central ni concede acceso al Portal. Al ingresar, el mecanismo existente vincula el ID central y actualiza nombre y apellido, conservando rol y estado locales. La pantalla explica esta diferencia.

La edición de la API permite rol, estado y email local. Rechaza cambios de identidad, `portal_user_id`, contraseñas, grupos y privilegios de Django. Los formularios existentes de Django admin conservan sus funciones técnicas, pero requieren el rol local ADMINISTRADOR; la identidad ya vinculada al Portal se muestra como sólo lectura.

Una cuenta desactivada ya no puede canjear tokens del Portal, aunque `PORTAL_AUTO_ENABLE_USERS` estuviera habilitado. Los access y refresh locales existentes también se rechazan mediante la autenticación que consulta la base en cada solicitud.

## Historial y protección administrativa

Desactivar sólo cambia `is_active`; conserva expedientes, responsables SIGEDoc, anulaciones y auditoría.

DELETE revisa todas las relaciones inversas actuales antes de borrar, incluidas las que podrían usar CASCADE o SET_NULL. Si hay expedientes, auditoría como actor, historial de contraseñas u otra actividad, devuelve 400 con la recomendación de desactivar. Una cuenta sin actividad puede eliminarse. La auditoría administrativa como usuario afectado conserva ID y username históricos aunque se elimine la cuenta.

El último ADMINISTRADOR activo no puede perder rol, desactivarse ni eliminarse. Tampoco se permite eliminar la propia cuenta. Las mutaciones de usuarios y el canje del Portal comparten un bloqueo transaccional sobre la fila del rol ADMINISTRADOR; PostgreSQL serializa estas operaciones. La API vuelve a verificar al actor después del bloqueo. Las comprobaciones de concurrencia real requieren PostgreSQL; SQLite no reproduce sus bloqueos.

Django admin requiere ADMINISTRADOR local además de sus requisitos técnicos de staff/activo, incluso si una cuenta de otro rol tiene is_superuser. Utiliza la misma protección del último administrador y las mismas comprobaciones de eliminación. Se deshabilita su eliminación masiva de usuarios. El catálogo de roles queda en consulta para impedir altas, cambios de nombre o desactivaciones que alteren la matriz fija.

`AuditoriaUsuario` registra USUARIO_CREADO, USUARIO_EDITADO, ROL_CAMBIADO, USUARIO_ACTIVADO, USUARIO_DESACTIVADO y USUARIO_ELIMINADO, con actor, afectado, fecha y datos de cambio. No guarda contraseñas ni tokens. Los cambios descriptivos de expedientes generan EDITAR_REGISTRO con valores anteriores/nuevos; no se permite cambiar número, año, origen o estado SIGEDoc por PATCH/PUT ni editar expedientes anulados.

## Archivos de esta implementación

- Backend: `roles/permissions.py`, `roles/admin.py`, `usuarios/administration.py`, `usuarios/models.py`, `usuarios/urls.py`, `usuarios/views/portal.py`, `usuarios/forms.py`, `usuarios/admin/usuario.py`.
- Django admin: `config/admin.py`, `config/admin_site.py`, `config/settings.py`.
- Expedientes: `agenda/views.py`, `agenda/urls.py`, `agenda/serializers.py`, `agenda/services.py`.
- Migraciones nuevas: `roles/migrations/0002_ensure_local_roles.py` y `usuarios/migrations/0002_auditoriausuario.py`.
- Frontend: nueva `src/pages/UsuariosPage.jsx`; cambios en `src/App.jsx`, `src/pages/RegistroPage.jsx`, `src/pages/ExpedienteDetail.jsx`, `src/components/AgendaForm.jsx`, `src/components/auth/SectionRoute.jsx`, `src/api/agenda.js`.
- Tests: nuevo `usuarios/test_administration.py`, nuevo `frontend/tests/roles.spec.js`; ajustes de `usuarios/tests.py`, `agenda/tests.py` y `frontend/tests/portal.spec.js`.

## Migraciones y puesta en marcha

Las migraciones nuevas aseguran la existencia de los tres roles sin reactivar roles deshabilitados y crean la tabla de auditoría. No asignan automáticamente un rol privilegiado a usuarios existentes.

No se ejecutaron migraciones sobre la base configurada en `.env`. Antes de aplicarlas hay que resolver el `InconsistentMigrationHistory` informado y los cambios previos de migraciones: `admin.0001_initial` figura aplicado sin `usuarios.0001_initial`; además, las migraciones históricas de agenda, roles e importación de usuarios estaban eliminadas al iniciar este trabajo. Se preservaron esas modificaciones previas. No usar `--fake` ni reiniciar una base con datos sin revisar su esquema e historial.

Con el historial ya consistente, desde `backend` ejecutar `python manage.py migrate`. Si aún no existe un administrador local, un operador autorizado debe asignar a una cuenta existente el `Rol` ADMINISTRADOR; `createsuperuser` por sí solo no asigna ese rol local. No se migra automáticamente a todos los superusuarios a ADMINISTRADOR.

## Validación

Las pruebas usan `config.test_settings`, una base SQLite en memoria, sin modificar la base de trabajo:

```powershell
python manage.py test --settings=config.test_settings
python manage.py makemigrations --check --dry-run --settings=config.test_settings
```

En `frontend`:

```powershell
npm run lint
npm run build
npm run test:e2e
```

La suite completa conserva una prueba antigua fallida: `LegacyUserMigrationTests` importa `usuarios.migrations.0002_import_legacy_users`, archivo eliminado previamente. No se restauró ni se ocultó esa prueba. Las cuatro pruebas existentes de concurrencia/triggers PostgreSQL se omiten con SQLite.

Resultado final: backend, 66 pruebas ejecutadas: 61 aprobadas, 4 omitidas por requerir PostgreSQL y 1 con el error previo de importación. Frontend, 20 pruebas de navegador aprobadas. Lint y compilación aprobados; Django no detecta cambios de modelos pendientes de migración. La nueva suite administrativa incluye 15 pruebas.
