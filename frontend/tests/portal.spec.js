import { test, expect } from '@playwright/test';

const session = {
  access: 'access-local-test', refresh: 'refresh-local-test', rol: 'CONSULTOR',
  has_changed_password: false,
  user: { id: 45, username: 'empleado.portal', nombre: 'Ana', apellido: 'Perez', rol_detalle: 'CONSULTOR' },
};

async function mockProtectedApi(page, role = 'CONSULTOR') {
  await page.route('**/api/expedientes/novedades/**', (route) => route.fulfill({ json: { cursor: 0, results: [] } }));
  await page.route('**/api/me/permisos/', (route) => route.fulfill({
    json: { rol: role, secciones: { agenda: { ver: true, escribir: role !== 'CONSULTOR', crear_registro: role !== 'CONSULTOR', editar_registro: role !== 'CONSULTOR', registrar_sigedoc: role !== 'CONSULTOR', anular_registro: role === 'ADMINISTRADOR' }, pendientes_sigedoc: { ver: role !== 'CONSULTOR' }, usuarios: { ver: role === 'ADMINISTRADOR' } } },
  }));
  await page.route(/\/api\/expedientes\/(?:\?.*)?$/, (route) => route.fulfill({ json: { count: 0, next: null, previous: null, results: [] } }));
  await page.route(/\/api\/expedientes\/pendientes-sigedoc\/(?:\?.*)?$/, (route) => route.fulfill({ json: { count: 0, next: null, previous: null, results: [] } }));
  await page.route(/\/api\/expedientes\/resumen\/(?:\?.*)?$/, (route) => route.fulfill({ json: {
    ultimo_numero_formateado: '15234/2026', pendientes: 4, registrados_hoy: 17, anulados: 1,
    anios: [2026, 2025], origenes: ['MESA_ENTRADA', 'SISTEMA_TRAMITES'],
    numeracion: { habilitado: true, anio: 2026, ultimo_numero_base: 15234, proximo_numero: 15235 },
  } }));
}

test('ingreso directo protegido ofrece login con redirect al receptor', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveURL(/\/portal-access$/);
  const href = await page.getByRole('link', { name: 'Ir al portal' }).getAttribute('href');
  const target = new URL(href);
  expect(target.origin).toBe('http://localhost:5173');
  expect(target.pathname).toBe('/login');
  expect(target.searchParams.get('redirect')).toBe('http://localhost:5176/portal-access');
  expect(target.searchParams.has('redirect_url')).toBe(false);
});

test('canje unico en StrictMode, URL limpia y Bearer local en solicitudes', async ({ page }) => {
  let exchanges = 0;
  let exchangeHeader;
  await mockProtectedApi(page);
  await page.addInitScript(() => sessionStorage.setItem('jwtToken', 'old-local-token'));
  await page.route('**/api/auth/portal-access/', async (route) => {
    exchanges += 1;
    expect(route.request().postDataJSON()).toEqual({ token: 'entrada-portal' });
    exchangeHeader = route.request().headers().authorization;
    await new Promise((resolve) => setTimeout(resolve, 100));
    await route.fulfill({ json: session });
  });
  const permissionRequest = page.waitForRequest('**/api/me/permisos/');
  await page.goto('/portal-access#portal_token=entrada-portal');
  await expect(page).toHaveURL('http://localhost:5176/');
  await expect(page.getByRole('heading', { name: 'Registro de Expedientes DPA' })).toBeVisible();
  expect(exchanges).toBe(1);
  expect(exchangeHeader).toBeUndefined();
  expect((await permissionRequest).headers().authorization).toBe('Bearer access-local-test');
  await expect(page.getByRole('button', { name: 'Registrar', exact: true })).toHaveCount(0);
  expect(await page.evaluate(() => sessionStorage.getItem('refreshToken'))).toBe('refresh-local-test');
});

test('error de canje limpia token de URL y no filtra credencial en pantalla', async ({ page }) => {
  await page.route('**/api/auth/portal-access/', (route) => route.fulfill({ status: 401, json: { detail: 'El token esta vencido.' } }));
  await page.goto('/portal-access?portal_token=secreto-de-prueba');
  await expect(page.getByRole('alert')).toHaveText('El token esta vencido.');
  await expect(page).toHaveURL('http://localhost:5176/portal-access');
  await expect(page.getByRole('link', { name: 'Ir al portal' })).toBeVisible();
  await expect(page.locator('body')).not.toContainText('secreto-de-prueba');
  expect(await page.evaluate(() => sessionStorage.getItem('jwtToken'))).toBeNull();
});

test('la query tiene prioridad sobre el fragmento', async ({ page }) => {
  await mockProtectedApi(page);
  await page.route('**/api/auth/portal-access/', (route) => {
    expect(route.request().postDataJSON().token).toBe('query-token');
    return route.fulfill({ json: session });
  });
  await page.goto('/portal-access?token=query-token#portal_token=fragmento-token');
  await expect(page).toHaveURL('http://localhost:5176/');
});

async function seedSession(page) {
  await page.addInitScript((payload) => {
    if (sessionStorage.getItem('e2eSeeded')) return;
    sessionStorage.setItem('e2eSeeded', 'true');
    sessionStorage.setItem('jwtToken', payload.access);
    sessionStorage.setItem('refreshToken', payload.refresh);
    sessionStorage.setItem('user', JSON.stringify(payload.user));
    sessionStorage.setItem('rolUser', payload.rol);
    sessionStorage.setItem('unrelated', 'conservar');
    localStorage.setItem('portal_refresh_token', 'legacy');
  }, session);
}

test('401 limpia sesion y vuelve al acceso sin bucle', async ({ page }) => {
  await seedSession(page);
  await page.route('**/api/me/permisos/', (route) => route.fulfill({ status: 401, json: { detail: 'Sesion vencida.' } }));
  await page.goto('/');
  await expect(page).toHaveURL(/\/portal-access$/);
  await expect(page.getByRole('link', { name: 'Ir al portal' })).toBeVisible();
  expect(await page.evaluate(() => sessionStorage.getItem('jwtToken'))).toBeNull();
});

test('403 muestra acceso denegado y conserva la sesion', async ({ page }) => {
  await seedSession(page);
  await mockProtectedApi(page);
  await page.route(/\/api\/expedientes\/(?:\?.*)?$/, (route) => route.fulfill({ status: 403, json: { detail: 'Sin acceso.' } }));
  await page.goto('/');
  await expect(page.getByRole('alert')).toHaveText('Tu rol no permite realizar esta operaci\u00f3n.');
  await expect(page).toHaveURL('http://localhost:5176/');
  expect(await page.evaluate(() => sessionStorage.getItem('jwtToken'))).toBe(session.access);
});

test('administrativo puede cargar desde el formulario', async ({ page }) => {
  await seedSession(page);
  await mockProtectedApi(page, 'ADMINISTRATIVO');
  await page.route('**/api/expedientes/manual/', (route) => route.fulfill({
    status: 201, json: { id: 1, numero: 15235, anio: 2026, numero_formateado: '15235/2026', origen: 'MESA_ENTRADA', estado_sigedoc: 'PENDIENTE', fecha_hora: '2026-10-05T12:00:00Z' },
  }));
  await page.goto('/');
  await page.getByRole('button', { name: '+ Nuevo registro' }).click();
  await page.getByRole('textbox', { name: /Causante/ }).fill('Juan Perez');
  await page.getByRole('textbox', { name: /Asunto/ }).fill('Nota');
  await page.getByRole('button', { name: 'Registrar', exact: true }).click();
  await expect(page.locator('[data-sonner-toast][data-type="success"]')).toContainText('Expediente N.\u00ba 15235/2026 creado correctamente.');
  await page.getByRole('button', { name: 'Ver expediente', exact: true }).click();
  await expect(page).toHaveURL('http://localhost:5176/expedientes/1');
});

test('reserva externa actualiza tabla e indicadores y avisa sin recargar', async ({ page }) => {
  await seedSession(page);
  await mockProtectedApi(page, 'ADMINISTRATIVO');
  let reserved = false;
  let delivered = false;
  let baseline = false;
  const record = { id: 901, numero: 15235, anio: 2026, numero_formateado: '15235/2026',
    origen: 'SISTEMA_TRAMITES', sistema_origen: 'TRAMITES', causante: 'Reserva automática',
    asunto: 'Línea de ribera', estado_sigedoc: 'PENDIENTE' };
  await page.route('**/api/expedientes/novedades/**', (route) => {
    const cursor = new URL(route.request().url()).searchParams.get('despues_id');
    if (cursor === null) {
      baseline = true;
      return route.fulfill({ json: { cursor: 900, results: [] } });
    }
    const results = reserved && !delivered ? [record] : [];
    if (results.length) delivered = true;
    return route.fulfill({ json: { cursor: delivered ? 901 : 900, results } });
  });
  await page.route(/\/api\/expedientes\/(?:\?.*)?$/, (route) => route.fulfill({ json: {
    count: reserved ? 1 : 0, next: null, results: reserved ? [record] : [],
  } }));
  await page.route(/\/api\/expedientes\/resumen\/(?:\?.*)?$/, (route) => route.fulfill({ json: {
    ultimo_numero_formateado: reserved ? '15235/2026' : '15234/2026', anios: [2026],
    origenes: ['SISTEMA_TRAMITES'], numeracion: { habilitado: true }, pendientes: reserved ? 1 : 0,
  } }));
  await page.route('**/api/expedientes/901/', (route) => route.fulfill({ json: { ...record, auditoria: [] } }));
  await page.goto('/');
  await expect.poll(() => baseline).toBe(true);
  await expect(page.locator('[data-sonner-toast]')).toHaveCount(0);
  reserved = true;
  await expect(page.locator('[data-sonner-toast]')).toContainText('Expediente N.º 15235/2026 reservado.', { timeout: 10000 });
  await expect(page.getByRole('cell', { name: 'Reserva automática', exact: true })).toBeVisible();
  await expect(page.locator('.stat-card').first()).toContainText('15235/2026');
  await page.getByRole('button', { name: 'Ver expediente', exact: true }).click();
  await expect(page).toHaveURL(/\/expedientes\/901$/);
});

test('logout limpia claves propias, conserva otras y navega al logout central', async ({ page, context }) => {
  await seedSession(page);
  await mockProtectedApi(page);
  await page.route('http://localhost:5173/logout', (route) => route.fulfill({ contentType: 'text/html', body: '<p>Logout central</p>' }));
  await page.goto('/');
  await page.getByRole('button', { name: /Ana Perez/ }).click();
  await page.getByRole('button', { name: 'Cerrar sesión', exact: true }).click();
  await expect(page).toHaveURL('http://localhost:5173/logout');
  const storage = await context.storageState();
  expect(storage.origins.find((item) => item.origin === 'http://localhost:5176')?.localStorage || []).not.toContainEqual({ name: 'portal_refresh_token', value: 'legacy' });
  await page.goto('/');
  await expect(page).toHaveURL(/\/portal-access$/);
  expect(await page.evaluate(() => sessionStorage.getItem('jwtToken'))).toBeNull();
  expect(await page.evaluate(() => sessionStorage.getItem('refreshToken'))).toBeNull();
  expect(await page.evaluate(() => sessionStorage.getItem('user'))).toBeNull();
  expect(await page.evaluate(() => sessionStorage.getItem('unrelated'))).toBe('conservar');
});

const expediente = {
  id: 837, numero: 15235, anio: 2026, numero_formateado: '15235/2026',
  causante: 'Juan Pérez', asunto: 'Línea de Ribera', tipo: 'LINEA_RIBERA',
  origen: 'SISTEMA_TRAMITES', sistema_origen: 'TRAMITES', referencia_externa: 'uuid-abc',
  fecha_hora: '2026-10-05T12:42:00Z', estado_sigedoc: 'PENDIENTE', anulado: false,
  auditoria: [{ id: 1, fecha_hora: '2026-10-05T12:42:00Z', accion: 'CREAR_REGISTRO', sistema: 'TRAMITES' }],
};

test('bloqueo del correlativo impide nuevas asignaciones en pantalla', async ({ page }) => {
  await seedSession(page);
  await mockProtectedApi(page, 'ADMINISTRATIVO');
  await page.route(/\/api\/expedientes\/resumen\/(?:\?.*)?$/, (route) => route.fulfill({ json: {
    pendientes: 1, registrados_hoy: 0, anulados: 0, anios: [2026], origenes: ['MESA_ENTRADA'],
    numeracion: { habilitado: false, anio: 2026, ultimo_numero_base: 1, proximo_numero: 2 },
  } }));
  await page.goto('/');
  await expect(page.getByText('Nuevas asignaciones bloqueadas')).toBeVisible();
  await expect(page.getByRole('button', { name: '+ Nuevo registro' })).toBeDisabled();
  await expect(page.getByText('2/2026', { exact: true })).toBeVisible();
});

test('busqueda y filtros envian numero, anio, estado y origen al backend', async ({ page }) => {
  await seedSession(page);
  await mockProtectedApi(page);
  const requests = [];
  await page.route(/\/api\/expedientes\/(?:\?.*)?$/, (route) => {
    requests.push(Object.fromEntries(new URL(route.request().url()).searchParams));
    return route.fulfill({ json: { count: 1, next: null, results: [expediente] } });
  });
  await page.goto('/');
  await page.getByRole('textbox', { name: 'Buscar expedientes' }).fill('15235');
  await page.getByRole('button', { name: 'Buscar', exact: true }).click();
  await page.getByLabel('Año', { exact: true }).selectOption('2026');
  await page.getByLabel('Origen', { exact: true }).selectOption('SISTEMA_TRAMITES');
  await page.getByRole('button', { name: 'Pendientes SIGEDoc', exact: true }).click();
  await expect.poll(() => requests.some((item) => item.q === '15235' && item.anio === '2026' && item.estado === 'PENDIENTE' && item.origen === 'SISTEMA_TRAMITES')).toBe(true);
  await expect(page.getByRole('link', { name: '15235/2026', exact: true })).toBeVisible();
});

test('pendientes solicita orden por antiguedad', async ({ page }) => {
  await seedSession(page);
  await mockProtectedApi(page, 'ADMINISTRATIVO');
  const requests = [];
  await page.route(/\/api\/expedientes\/pendientes-sigedoc\/(?:\?.*)?$/, (route) => {
    requests.push(Object.fromEntries(new URL(route.request().url()).searchParams));
    return route.fulfill({ json: { count: 1, next: null, results: [expediente] } });
  });
  await page.goto('/pendientes-sigedoc');
  await expect(page.getByRole('heading', { name: 'Pendientes SIGEDoc', exact: true })).toBeVisible();
  await expect.poll(() => requests.some((item) => item.estado === 'PENDIENTE' && item.orden === 'fecha_asc')).toBe(true);
  await expect(page.getByRole('columnheader', { name: 'Tiempo pendiente' })).toBeVisible();
});

test('SIGEDoc exige confirmacion y conserva el mismo numero', async ({ page }) => {
  await seedSession(page);
  await mockProtectedApi(page, 'ADMINISTRATIVO');
  await page.route('**/api/expedientes/837/', (route) => route.fulfill({ json: expediente }));
  let confirms = 0;
  await page.route('**/api/expedientes/837/registrar-sigedoc/', (route) => {
    confirms += 1;
    expect(route.request().postDataJSON()).toEqual({ confirmar: true });
    return route.fulfill({ json: { ...expediente, estado_sigedoc: 'REGISTRADO', fecha_registro_sigedoc: '2026-10-05T14:14:00Z', registrado_sigedoc_por_nombre: 'Ana Pérez' } });
  });
  await page.goto('/expedientes/837');
  await page.getByRole('button', { name: /Marcar como registrado/ }).click();
  expect(confirms).toBe(0);
  await expect(page.getByRole('dialog')).toContainText('15235/2026');
  await page.getByRole('button', { name: 'Confirmar', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  expect(confirms).toBe(1);
  await expect(page.getByRole('heading', { name: 'Expediente N.º 15235/2026' })).toBeVisible();
});

test('anulacion requiere motivo y deja el numero visible', async ({ page }) => {
  await seedSession(page);
  await mockProtectedApi(page, 'ADMINISTRADOR');
  await page.route('**/api/expedientes/837/', (route) => route.fulfill({ json: expediente }));
  await page.route('**/api/expedientes/837/anular/', (route) => {
    expect(route.request().postDataJSON()).toEqual({ motivo: 'Presentación duplicada' });
    return route.fulfill({ json: { ...expediente, anulado: true, motivo_anulacion: 'Presentación duplicada', fecha_anulacion: '2026-10-05T14:30:00Z', anulado_por_nombre: 'Ana Pérez' } });
  });
  await page.goto('/expedientes/837');
  await page.getByRole('button', { name: 'Anular registro', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Confirmar', exact: true })).toBeDisabled();
  await page.getByRole('textbox', { name: 'Motivo obligatorio' }).fill('Presentación duplicada');
  await page.getByRole('button', { name: 'Confirmar', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.getByRole('heading', { name: 'Expediente N.º 15235/2026' })).toBeVisible();
});

test('listado del registro muestra los datos y estados administrativos', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await seedSession(page);
  await mockProtectedApi(page, 'ADMINISTRATIVO');
  await page.route(/\/api\/expedientes\/(?:\?.*)?$/, (route) => route.fulfill({ json: {
    count: 3, next: null, results: [
      expediente,
      { ...expediente, id: 838, numero: 15234, numero_formateado: '15234/2026', origen: 'MESA_ENTRADA', causante: 'Municipalidad', asunto: 'Nota administrativa', estado_sigedoc: 'REGISTRADO' },
      { ...expediente, id: 839, numero: 15233, numero_formateado: '15233/2026', causante: 'María Gómez', anulado: true },
    ],
  } }));
  await page.goto('/');
  await expect(page.getByRole('cell', { name: 'Juan Pérez' })).toBeVisible();
  await expect(page.getByRole('cell', { name: 'Anulado', exact: true })).toBeVisible();
  await page.screenshot({ path: test.info().outputPath('registro-expedientes.png'), fullPage: true });
});
