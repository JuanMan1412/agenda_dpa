# Registro de Expedientes DPA

## Resultado y condición de habilitación

Agenda evolucionó sobre su tabla existente a un registro administrativo con numeración anual, acceso del Portal DPA, integración de servicios, estados SIGEDoc, anulación y auditoría. Mesa de Entrada y Trámites usan el mismo contador; no existe un segundo número para SIGEDoc.

Estado verificado en la base local `agenda_db` tras la migración:

| Dato | Valor |
| --- | --- |
| Registros históricos conservados | 1 |
| Último número en Agenda | 1/2026 |
| Último número consumido en el contador anual | 1/2026 |
| Próximo número propuesto | **2/2026** |
| Nuevas asignaciones | **Bloqueadas** |

El próximo número propuesto no se habilitó. Se debe comparar con el último número REAL del libro de Mesa de Entrada y confirmar expresamente. El backend rechaza nuevas altas manuales y externas con 409 mientras el control no esté habilitado. La consulta de históricos sigue disponible. Un reintento de una reserva ya existente devuelve su expediente incluso si las nuevas altas están bloqueadas.

## Análisis del sistema anterior

`Agenda` sólo tenía `id`, `numero`, `letra`, `origen`, `referencia_externa` y `fecha_hora`; no tenía año, causante, asunto, estados o auditoría. PostgreSQL asignaba `numero` mediante la secuencia global `agenda_numero_seq`. No existía reinicio anual ni idempotencia. Había un registro manual con número 1 y la secuencia proponía 2. La autenticación vigente era Portal DPA, con `usuarios.User`, roles locales y API keys para servicios.

Se conservaron el modelo Django `Agenda`, la tabla física `agenda`, IDs, números, letras, referencias y fechas. El nombre conceptual `RegistroExpediente` es un alias del mismo modelo: no crea otra tabla ni otro correlativo. Se mantienen las rutas anteriores y la autenticación ya implementada.

## Modelos finales

### Agenda / RegistroExpediente

| Grupo | Campos |
| --- | --- |
| Identidad administrativa | `id`, `numero`, `anio`, `letra` histórica |
| Registro | `fecha_hora`, `causante`, `asunto`, `tipo` |
| Origen e integración | `origen`, `sistema_origen`, `referencia_externa`, `referencia_idempotencia` |
| SIGEDoc | `estado_sigedoc`, `fecha_registro_sigedoc`, `registrado_sigedoc_por` |
| Autor | `creado_por` |
| Anulación | `anulado`, `fecha_anulacion`, `anulado_por`, `motivo_anulacion` |
| Fechas técnicas | `created_at`, `updated_at` |

`fecha_registro` en la respuesta es un alias de `fecha_hora`; no duplica la fecha en la base. `numero_formateado` se calcula como `numero/anio`. El frontend y los sistemas externos no pueden enviar número, año, origen, autores, fechas o estados en las altas.

Estados SIGEDoc: `PENDIENTE` y `REGISTRADO`. La anulación es independiente: un expediente registrado puede anularse conservando su registración y todo su historial. Un expediente anulado no puede marcarse como registrado. Anular no borra el registro ni devuelve el número al contador.

Restricciones: `UNIQUE(numero, anio)`, número positivo, referencia única por sistema y clave de idempotencia única por sistema. Las referencias de integraciones históricas desconocidas se conservan sin atribuirles arbitrariamente un sistema.

### Modelos de control

- `CorrelativoAnual`: una fila por año, con `ultimo_numero`.
- `ControlNumeracion`: control único de habilitación, año validado, último número físico confirmado, usuario y fecha de confirmación.
- `AuditoriaExpediente`: expediente, usuario o sistema, fecha, acción, datos relevantes y motivo. Acciones principales: `CREAR_REGISTRO`, `REGISTRAR_SIGEDOC`, `ANULAR_REGISTRO`. También se registran `MIGRAR_HISTORICO` y `CONFIRMAR_CORRELATIVO`.

Los usuarios de auditoría están protegidos contra borrado mediante relaciones `PROTECT`. El admin permite consultar los registros, contadores y auditoría; no permite editar números, borrar expedientes o modificar el contador.

## Correlativo, concurrencia e idempotencia

El backend calcula el año con `America/Argentina/Buenos_Aires`. A las 00:00 locales del nuevo año, la primera alta usa su fila de contador y obtiene 1; no existe una tarea programada que reinicie contadores anteriores.

La creación funciona dentro de `transaction.atomic`:

1. Bloquear las claves de referencia/idempotencia con `pg_advisory_xact_lock`, en orden estable.
2. Consultar si ya existe el expediente. Si existe, devolverlo antes de consultar o crear el contador del año.
3. Verificar la habilitación de nuevas asignaciones.
4. Calcular el año actual y obtener su bloqueo transaccional. Este bloqueo también cubre la primera solicitud cuando aún no existe la fila anual.
5. Obtener y bloquear la fila del contador con `select_for_update`.
6. Crear el expediente, avanzar el contador y escribir la auditoría en la misma transacción.
7. Confirmar todo junto. Una falla revierte expediente, contador y auditoría.

Las restricciones únicas de PostgreSQL respaldan los bloqueos. No se utiliza `MAX(numero)+1` para asignar números en solicitudes. Los máximos se consultan únicamente para mostrar el estado o migrar/confirmar el piso del contador.

La idempotencia externa usa `(sistema_origen, referencia_externa)`, obligatoria para cada solicitud; opcionalmente admite `Idempotency-Key`. La manual también admite ese header y el frontend genera una clave por formulario, conservándola después de un error de red. Un reintento idéntico devuelve 200, el mismo ID y número, sin avanzar el contador ni repetir la auditoría. Datos distintos para la misma referencia devuelven 409. La referencia y la clave no pueden señalar dos expedientes distintos.

La identidad del sistema procede de su credencial. Trámites no puede reservar en nombre de Obras ni consultar un expediente ajeno. Una reserva del 31/12/2026 reintentada el 01/01/2027 conserva su número de 2026; no consume un número de 2027. También se conserva el expediente original si fue anulado.

Un trigger PostgreSQL impide el `DELETE` físico y la modificación de `numero` o `anio` de registros existentes. No hay endpoints de edición general ni borrado.

## API local y permisos

Todas las rutas locales requieren el Bearer JWT emitido por este backend; conservan la identidad central del Portal y el rol ORM actual de `usuarios.User`.

| Método y ruta | Uso |
| --- | --- |
| `GET /api/expedientes/` | Listado paginado, 25 filas por página, máximo 100 |
| `GET /api/expedientes/resumen/` | Indicadores, años, orígenes y estado de habilitación del correlativo |
| `POST /api/expedientes/manual/` | Crear un registro manual con causante y asunto obligatorios |
| `GET /api/expedientes/{id}/` | Detalle y auditoría |
| `POST /api/expedientes/{id}/registrar-sigedoc/` | Confirmar registro con `{"confirmar": true}` |
| `POST /api/expedientes/{id}/anular/` | Anular con `{"motivo": "..."}` obligatorio |
| `GET /api/me/permisos/` | Permisos locales por sección y acción |

Filtros de listado: `q` (número, `numero/anio`, causante, asunto o referencia), `anio`, `origen`, `estado=TODOS/PENDIENTE/REGISTRADO/ANULADO`, `hoy=true`, `orden=fecha_asc/numero_desc`, `page` y `page_size`. Pendientes y registrados excluyen anulados. `hoy` filtra por fecha de alta; el indicador **Registrados hoy** cuenta confirmaciones SIGEDoc de hoy. Las fechas se interpretan en horario argentino.

| Rol | Consultar | Crear | Registrar SIGEDoc | Anular |
| --- | --- | --- | --- | --- |
| CONSULTOR | Sí | No | No | No |
| ADMINISTRATIVO | Sí | Sí | Sí | No |
| ADMINISTRADOR | Sí | Sí | Sí | Sí |

Un rol desconocido o deshabilitado no obtiene permisos. “Mesa de Entrada” sigue siendo una oficina y una denominación de origen, no un rol. Los permisos se aplican en el backend, incluida cada acción personalizada; la UI sólo refleja esos permisos.

Compatibilidad: `GET /api/agenda/` sigue devolviendo una lista sin paginación. `/api/agenda/manual/` y `/api/agenda/reservar/` apuntan a los servicios nuevos. Sus consumidores deben adaptar el cuerpo para aportar causante/asunto y, en reservas externas, referencia obligatoria. Se acepta `referencia_externa` como alias de `referencia`, y se conserva `letra` opcional. No se generan expedientes nuevos incompletos por compatibilidad con cuerpos antiguos.

## Integración de Trámites

El Registro no importa modelos, workflows, oficinas ni documentos de Trámites.

Credencial: `X-Api-Key`. Configuración backend, sin secretos en código o variables Vite:

```dotenv
EXPEDIENTES_API_KEYS={"CLAVE_PROPIA": {"sistema": "TRAMITES", "permisos": ["reservar", "consultar"]}}
```

Se generó una credencial local en `backend/.env`; su valor no se muestra en la documentación, pruebas ni logs. Obtenerlo allí y configurarlo únicamente en el backend de Trámites. Otros sistemas pueden añadirse al mismo objeto, con credenciales independientes. También se admite `AGENDA_API_KEYS` del esquema previo, cuyo formato string otorga `reservar` y `consultar`; es preferible usar el nuevo formato para permisos explícitos.

Reserva:

```http
POST /api/integraciones/expedientes/reservar/
X-Api-Key: CLAVE_PROPIA
Content-Type: application/json

{
  "sistema": "TRAMITES",
  "referencia": "uuid-del-tramite",
  "causante": "Juan Pérez",
  "asunto": "Línea de Ribera",
  "tipo": "LINEA_RIBERA"
}
```

Respuesta 201 (200 para reintentos):

```json
{
  "id": 837,
  "numero": 15235,
  "anio": 2026,
  "numero_formateado": "15235/2026",
  "estado_sigedoc": "PENDIENTE"
}
```

La respuesta real incluye además los demás campos del registro. `sistema` es opcional; si se envía, debe coincidir con la credencial. El número y año nunca se envían en la solicitud.

Consulta autenticada del propio sistema:

- `GET /api/integraciones/expedientes/{id}/`.
- `GET /api/integraciones/expedientes/por-referencia/?referencia=uuid-del-tramite`.

Errores: 400 para campos inválidos/no permitidos; 401 para credencial ausente o inválida; 403 para permisos o identidad de sistema incorrectos; 404 para expedientes ajenos/no existentes; 409 para altas bloqueadas, conflicto idempotente o transición administrativa incompatible. Las credenciales externas no permiten marcar SIGEDoc, anular, cambiar números o modificar el correlativo.

## Frontend

- `/`: título Registro de Expedientes DPA, cuatro indicadores, búsqueda, filtros, tabla y paginación.
- `/pendientes-sigedoc`: excluye anulados y ordena por antigüedad; muestra tiempo pendiente con actualización cada minuto.
- `/expedientes/{id}`: datos, referencia de origen, número único a utilizar en SIGEDoc, responsables y auditoría.
- Formulario **Nuevo registro**: causante/asunto obligatorios, categoría opcional y fecha informativa automática. No pide número ni año. Al confirmar muestra el expediente creado y su enlace.
- Confirmación explícita antes de marcar SIGEDoc; anulación con motivo y confirmación.
- Botón de alta bloqueado y aviso con último/próximo número mientras falta validar el libro.
- Menú de perfil, logout central, rutas protegidas y cliente Bearer conservados. Los datos se invalidan después de crear, registrar o anular.

## Migraciones aplicadas y preservación

Las migraciones se aplicaron en la base local sin borrar registros:

- `agenda.0003_correlativoanual_alter_agenda_options_and_more`: crea modelos de control/auditoría y toma la gestión del esquema existente mediante migraciones de Django.
- `agenda.0004_agenda_anio_agenda_anulado_agenda_anulado_por_and_more`: agrega campos, retira la asignación por defecto de la secuencia global, migra orígenes, deriva años de las fechas locales, preserva timestamps históricos, crea auditoría de migración y restricciones por año/referencia.
- `agenda.0005_preserve_administrative_records`: instala la protección PostgreSQL de números y borrado.

La secuencia anterior permanece como referencia histórica, pero ya no asigna números. El contador conserva el piso consumido de la secuencia para el año vigente cuando existen registros de ese año, incluidos números consumidos sin fila. No se reinicia ni reduce automáticamente. Los históricos sin causante/asunto se muestran como datos no disponibles; no se inventan identidades, metadata o confirmaciones SIGEDoc. Su estado inicial es pendiente para revisión.

Antes de migrar se creó una copia local en `backend/.local-backups/agenda_antes_registro_expedientes.json`, excluida de Git. Se comprobó después que ID, número, letra, referencia y fecha de cada registro coinciden con esa copia. Esa copia es adicional: al desplegar, realizar también un respaldo completo de PostgreSQL. Las migraciones administrativas son irreversibles deliberadamente; no intentar deshacerlas borrando expedientes.

## Confirmación y despliegue

Consulta sin modificaciones:

```powershell
& .\backend\venv\Scripts\python.exe .\backend\manage.py confirmar_correlativo
```

Después de comparar manualmente con el libro, ejecutar exclusivamente con los valores reales confirmados:

```powershell
& .\backend\venv\Scripts\python.exe .\backend\manage.py confirmar_correlativo --anio 2026 --ultimo-numero-libro NUMERO_REAL --usuario ADMIN_LOCAL --confirmar
```

No se ejecutó este segundo comando en la base real. Requiere un administrador local activo, el año vigente y un número físico que no sea inferior al piso consumido. Puede avanzar el contador si el libro físico está más adelante, nunca reducirlo. Guarda quién confirmó, cuándo, el número físico y la propuesta siguiente. Si los valores no coinciden, resolver primero esa diferencia; no considerar los datos de demostración como libro real.

Una vez habilitada la numeración, los años nuevos se inicializan automáticamente en 1; el control no necesita una tarea de reinicio anual. No hay ninguna variable `.env` que habilite las altas saltándose esta confirmación.

En despliegue:

1. Detener temporalmente escrituras y verificar/resguardar la base existente.
2. Instalar `backend/requirements.txt`. Si todavía usa `auth.User`, aplicar primero la transición específica: `manage.py migrate usuarios --settings=config.legacy_user_migration_settings`.
3. Ejecutar `manage.py migrate` con los settings normales.
4. Verificar `manage.py check`, históricos y `confirmar_correlativo` sin `--confirmar`.
5. Compilar el frontend con `npm.cmd ci` y `npm.cmd run build`; servir su `index.html` para las rutas profundas.
6. Configurar hosts/CORS y credenciales del Portal y de Trámites mediante los `.env.example`.
7. Comparar el contador con el libro y confirmar expresamente antes de habilitar nuevas asignaciones.

Backend de desarrollo: `manage.py runserver 8000`. Frontend: `npm.cmd run dev` desde `frontend`, puerto 5174. El código del Portal continúa siendo `agenda`; un cambio del código central requiere coordinar su registro y las variables de ambos proyectos.

## Verificación realizada

**51 pruebas backend con PostgreSQL real**, en una base de pruebas separada que se elimina al terminar, sin modificar `agenda_db`. Incluyen:

- Altas manuales/externas en el mismo contador y estado inicial pendiente.
- Solicitudes simultáneas distintas y reintentos simultáneos de la misma referencia.
- Primeras solicitudes concurrentes del nuevo año; límite anual en horario argentino.
- Idempotencia manual, externa, entre años y de expedientes anulados.
- Registración SIGEDoc con fecha/autor y sin auditoría duplicada.
- Anulación con permisos/motivo y número no reutilizable.
- Protección del número y del borrado en PostgreSQL.
- Validación de credenciales, identidad de sistemas y consultas propias.
- Búsqueda/filtros/paginación, bloqueo inicial y confirmación que no retrocede.
- Rollback del contador si falla la auditoría.
- Autenticación Portal, modelos usuarios/roles, migración de usuarios y pantallas del admin.

**14 pruebas de navegador con Chrome**, con API simulada: login/callback, canje único, sesión, errores 401/403, alta manual, bloqueo, filtros, pendientes, confirmación SIGEDoc, anulación y vista principal. Se inspeccionó visualmente la captura del listado. No simulan una registración real en SIGEDoc ni afirman que exista una conexión automática con ese producto: la confirmación la realiza Mesa de Entrada tras operar allí.

```powershell
& .\backend\venv\Scripts\python.exe .\backend\manage.py test agenda usuarios --noinput
& .\backend\venv\Scripts\python.exe .\backend\manage.py check
& .\backend\venv\Scripts\python.exe .\backend\manage.py makemigrations --check --dry-run
cd frontend
npm.cmd run lint
npm.cmd run build
npm.cmd run test:e2e
```

SQLite está disponible únicamente para pruebas funcionales: `--settings=config.test_settings`. Las cuatro pruebas de concurrencia/protección PostgreSQL se omiten con SQLite; las evidencias anteriores provienen de ejecutarlas también sobre PostgreSQL.

## Archivos modificados

Backend: `agenda/models.py`, `services.py`, `authentication.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`, `apps.py`, `tests.py`, migraciones 0003–0005, comando `confirmar_correlativo`, `roles/permissions.py`, `usuarios/tests.py`, `config/settings.py` y `.env.example`. Se conservan la app y los modelos de usuarios/roles existentes.

Frontend: `App.jsx`, `api/agenda.js`, `components/AgendaForm.jsx`, `AgendaTable.jsx`, `EstadoExpediente.jsx`, `layout/Topbar.jsx`, `pages/RegistroPage.jsx`, `ExpedienteDetail.jsx`, `PortalAccess.jsx`, helpers de expedientes, `index.css`, pruebas de navegador y `.env.example`. Se mantienen el cliente HTTP, la sesión y los providers existentes.

Repositorio: `.gitignore`, este documento y la actualización de `INTEGRACION_PORTAL.md`.

## Decisiones pendientes

- **Obligatoria:** confirmar el último número real del libro físico. El sistema conserva el bloqueo hasta esa confirmación.
- Configurar la credencial generada en el backend real de Trámites y comprobar una reserva/reintento/consulta desde ese consumidor.
- Revisar el dato y estado SIGEDoc del registro histórico; no se supusieron datos faltantes.
- Verificar el acceso real desde la tarjeta del Portal y las rutas del hosting al desplegar. El backend del Registro está implementado; no se modificaron proyectos externos.
