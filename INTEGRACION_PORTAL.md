# Autenticación de Agenda DPA

La aplicación evolucionó a **Registro de Expedientes DPA**. La autenticación descrita aquí se conserva; el modelo administrativo, los permisos por acción y los contratos actuales se documentan en [REGISTRO_EXPEDIENTES.md](REGISTRO_EXPEDIENTES.md).

Se implementó el contrato de `REPLICAR_AUTENTICACION_PORTAL.md` para la agenda. El frontend de Agenda usa `http://localhost:5174`, su backend `http://localhost:8000`, el frontend central `http://localhost:5173` y la API central `http://localhost:8001/api`.

## Configuración y arranque

Los valores locales se leen de `backend/.env` y `frontend/.env`, excluidos de Git. Los `.env.example` contienen únicamente nombres y ejemplos sin secretos. Las variables del proceso tienen prioridad sobre el `.env` del backend.

`SIGNING_KEY` es obligatoria y debe coincidir con la clave HS256 del portal. `PORTAL_SYSTEM_CODE=agenda` también es obligatorio. `PORTAL_DEFAULT_ROLE=CONSULTOR` define el rol inicial y `PORTAL_AUTO_ENABLE_USERS` permite o impide reactivar cuentas locales deshabilitadas. `ENVIRONMENT=L`, `LOCAL`, `DEV` o `DEVELOPMENT` activa DEBUG; `DJANGO_DEBUG` permite modificarlo explícitamente. Configurar `ALLOWED_HOSTS` y orígenes propios al desplegar.

El login se configura en `VITE_PORTAL_LOGIN_URL=http://localhost:5173/login`; si se recibe la raíz del portal, el helper agrega `/login`. El callback usa el origen de Agenda y el parámetro `redirect`. `VITE_PORTAL_API_URL` se conserva, pero este flujo no llama directamente a la API central.

Desde la raíz del repositorio, en PowerShell:

```powershell
& .\backend\venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
& .\backend\venv\Scripts\python.exe .\backend\manage.py migrate
& .\backend\venv\Scripts\python.exe .\backend\manage.py runserver 8000
```

En otra terminal:

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev
```

Vite utiliza el puerto 5174 con `strictPort`: no cambia silenciosamente a otro origen incompatible con CORS. Reiniciar Vite después de cambiar su `.env`.

## Usuarios y permisos locales

`usuarios` y `roles` están registradas en `INSTALLED_APPS`, y `AUTH_USER_MODEL='usuarios.User'`. La identidad central se guarda en `usuarios.User.portal_user_id`, el nombre exacto en `nombre_completo` y el rol en la relación con `roles.Rol`. La autenticación está en `usuarios/authentication.py`, el canje y refresh en `usuarios/views/portal.py`, y los permisos de agenda en `roles/permissions.py`. `portal_accounts` ya no es una aplicación activa; sólo se conservan sus archivos de migración históricos. El módulo de referencia `utils` no se utiliza para proteger la agenda.

| Rol local | Consultar agenda | Registrar manualmente |
| --- | --- | --- |
| CONSULTOR | Sí | No |
| ADMINISTRATIVO | Sí | Sí |
| ADMINISTRADOR | Sí | Sí |
| Rol desconocido o perfil ausente | No | No |

El rol del portal no asigna privilegios locales. El primer ingreso crea una cuenta activa con contraseña inutilizable y el rol configurado; el flag de autoactivación gobierna solamente la reactivación de cuentas existentes. Un segundo ingreso conserva el rol local. La coincidencia por username nunca reemplaza un ID central distinto; las colisiones se rechazan con 403. Las cuentas locales `is_staff` o `is_superuser` sin vínculo requieren asociar manualmente su perfil antes del canje.

Administrar los usuarios y sus roles desde `/admin/`, en las apps **Usuarios** y **Roles**. Para crear un administrador Django local, ejecutar `manage.py createsuperuser`; no se creó ninguna cuenta ni contraseña administrativa automáticamente. Asignar `ADMINISTRATIVO` o `ADMINISTRADOR` en el usuario para habilitar la carga manual. Desactivar el usuario bloquea sus access y refresh existentes inmediatamente; deshabilitar el rol bloquea sus permisos. El ID del portal puede vincularse manualmente desde la edición del usuario.

`GET /api/me/permisos/` devuelve el rol y los permisos de la sección `agenda`. La respuesta de canje conserva los campos del contrato: `user.rol` es el ID de `roles.Rol` y `rol_detalle` su descripción. El nombre exacto está en `nombre_completo`; `nombre` y `apellido` separan el último término como apellido. Se conserva el documento local si ya existe.

## Endpoints y sesión

- `POST /api/auth/portal-access/`: público, sin autenticar un Bearer previo. Valida firma, vencimiento, tipo access, identidad central y acceso a `agenda`. Sincroniza dentro de una transacción y devuelve tokens con el ID local.
- `GET /api/me/permisos/`, `GET /api/agenda/` y `POST /api/agenda/manual/`: requieren access local; el backend aplica permisos, incluida la escritura manual.
- `POST /api/auth/token/refresh/`: acepta exclusivamente refresh local y consulta el estado y rol actuales. El frontend almacena el refresh, pero ante 401 limpia la sesión y vuelve a `/portal-access`; no renueva automáticamente.
- `POST /api/agenda/reservar/`: conserva el contrato servidor a servidor por `X-Api-Key`, con claves configuradas mediante `AGENDA_API_KEYS`. Un JWT de navegador no reemplaza esa credencial.

Los tokens locales contienen `local_system`, el vínculo central, el ID local y los claims de rol/sistemas. El autenticador rechaza directamente los tokens centrales en las rutas privadas y consulta `usuarios.User` y su rol en cada petición. Access local dura 15 minutos y refresh local un día.

`PortalAccess` acepta los alias de la guía y prioriza query sobre fragmento. Borra la credencial de la URL al comenzar, incluso si el canje falla; no la muestra ni registra. Comparte una sola promesa entre las ejecuciones de StrictMode y evita guardar sesión después del desmontaje. Un 403 muestra acceso denegado sin cerrar la sesión.

El desplegable del perfil contiene **Cerrar sesión**. Evita clics repetidos, borra las claves de sesión propias y el caché de React Query, conserva otros datos del navegador y navega mediante `location.replace` a `/logout` del frontend central. Ese frontend es responsable de revocar su refresh y llegar a `/login`. El receptor no puede borrar almacenamiento de otro origen. El logout no revoca access ya emitidos: vencen normalmente; no se implementó logout global de otros sistemas.

## Migraciones y base de datos

Se aplicaron las migraciones en `agenda_db`, que estaba vacía, según la confirmación del usuario:

- Migraciones estándar de Django para auth, admin, sesiones y contenttypes.
- `portal_accounts/0001_initial`: migración histórica de la implementación inicial, conservada sin registrar la app.
- `roles/0001_initial` y `0002_seed_agenda_roles`: crean los roles locales y cargan CONSULTOR, ADMINISTRATIVO y ADMINISTRADOR.
- `usuarios/0001_initial`: crea el modelo de usuario existente y su historial de contraseñas.
- `usuarios/0002_import_legacy_users`: traslada las cuentas de `auth_user` y los vínculos de la tabla anterior, preservando IDs, hashes de contraseñas, roles, estado, grupos y permisos; ajusta la relación del historial del admin en PostgreSQL.
- `agenda/0001_initial`: registra el estado del modelo existente con `managed=False`.
- `agenda/0002_initialize_table`: crea `agenda` y `agenda_numero_seq` solamente si falta la tabla; mantiene la numeración y fecha asignadas por PostgreSQL. No reemplaza ni modifica una tabla de agenda existente. Su reversión conserva la tabla de negocio.

No se copiaron migraciones de Móvil, ni usuarios, contraseñas o registros de otra base. La evolución del Registro conserva la tabla `agenda` y pasa su esquema a migraciones de Django; consultar las migraciones 0003–0005 y el documento del Registro.

La transición en esta base ya está aplicada. Las tablas anteriores se conservan como respaldo, pero el sistema utiliza `usuarios_user` y `roles_rol`. Para otra instalación que ya tenga las migraciones del admin aplicadas con `auth.User`, ejecutar primero:

```powershell
& .\backend\venv\Scripts\python.exe .\backend\manage.py migrate usuarios --settings=config.legacy_user_migration_settings
& .\backend\venv\Scripts\python.exe .\backend\manage.py migrate
```

Los settings de transición se usan únicamente para esa migración; no sirven para arrancar el servidor. En una base nueva, usar directamente `manage.py migrate` con los settings normales.

## Registro en el portal y despliegue

La contraparte central debe tener el sistema con código **agenda**, URL `http://localhost:5174` y acceso asignado al usuario/oficina. Su tarjeta debe lanzar `/portal-access#portal_token=...`; si usa `SYSTEM_LAUNCH_OPTIONS_BY_CODE`, configurar `pathName: '/portal-access'` y `forceTokenLaunch: true` para `agenda`. No duplicar la ruta en la URL guardada.

No se modificó el proyecto central desde este repositorio. La configuración de su registro y su revocación de refresh requieren comprobarse con el portal real. En producción, el servidor del frontend debe servir `index.html` al recargar `/portal-access`; esta implementación asume publicación en la raíz del dominio, no en un subdirectorio.

## Verificaciones

```powershell
& .\backend\venv\Scripts\python.exe .\backend\manage.py check
& .\backend\venv\Scripts\python.exe .\backend\manage.py makemigrations --check --dry-run
& .\backend\venv\Scripts\python.exe .\backend\manage.py test usuarios --settings=config.test_settings
cd frontend
npm.cmd run lint
npm.cmd run build
npm.cmd run test:e2e
```

Las 28 pruebas backend usan SQLite en memoria, sin tocar los datos locales: alta, reingreso, nombres, vínculos y colisiones, firma y vencimiento, tipo de token, cuerpo e identidad inválidos, acceso al sistema, configuración obligatoria, autoactivación, protección de lectura/escritura, cambios de rol/estado, refresh local y API keys externas. Incluyen el modelo `usuarios.User`, roles deshabilitados y la conservación de cuentas mediante la migración de transición.

También se verificaron la carga manual y la reserva externa con SQL real de PostgreSQL sobre tablas y secuencias temporales. La numeración resultó correlativa y los registros reales de agenda permanecieron intactos.

Las 8 pruebas de navegador usan Chrome en Windows y APIs simuladas: callback al receptor, canje único con StrictMode, limpieza de URL, Bearer local, errores 401/403, permisos de consulta/carga y limpieza/redirección del logout. En otros sistemas instalar Chromium con `npx playwright install chromium`. Las pruebas no hacen login ni logout en una sesión central real y no demuestran la revocación del portal. Completar la prueba manual entrando desde su tarjeta y cerrando sesión desde el perfil.

El entorno virtual del proyecto tiene sus dependencias instaladas. El Python global presentaba un driver PostgreSQL incompatible; utilizar el Python de `backend/venv`. PyJWT advierte que la clave compartida configurada es corta; cualquier cambio de esa clave debe coordinarse con el portal.

## Archivos principales

- Backend: `config/settings.py`, `config/urls.py`, `agenda/views.py`, `agenda/migrations/`, `usuarios/`, `roles/`, `config/legacy_user_migration_settings.py`, `config/test_settings.py`, `requirements.txt` y `.env.example`.
- Frontend: `App.jsx`, `main.jsx`, `services/api.js`, `api/agenda.js`, `pages/PortalAccess.jsx`, `components/auth/`, `components/layout/Topbar.jsx`, `contexts/`, helpers de sesión/URLs/requests, estilos, configuración de Vite, dependencias y pruebas Playwright.
- Repositorio: `.gitignore` incluye entornos, archivos secretos y resultados generados de las pruebas.
