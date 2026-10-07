import { test, expect } from '@playwright/test';

async function setup(page, role) {
  await page.route('**/api/expedientes/novedades/**', (route) => route.fulfill({ json: { cursor: 0, results: [] } }));
  await page.addInitScript(() => {
    sessionStorage.setItem('jwtToken', 'local-test');
    sessionStorage.setItem('user', JSON.stringify({ id: 1, username: 'admin' }));
  });
  const write = role !== 'CONSULTOR';
  await page.route('**/api/me/permisos/', (route) => route.fulfill({ json: { rol: role, secciones: {
    agenda: { ver: true, crear_registro: write, editar_registro: write, registrar_sigedoc: write, anular_registro: role === 'ADMINISTRADOR' },
    pendientes_sigedoc: { ver: write }, usuarios: { ver: role === 'ADMINISTRADOR' },
  } } }));
  await page.route(/\/api\/expedientes\/(?:\?.*)?$/, (route) => route.fulfill({ json: { count: 1, results: [{ id: 1, numero_formateado: '1/2026', causante: 'Persona', asunto: 'Nota', estado_sigedoc: 'PENDIENTE', acciones_disponibles: { editar: write } }], next: null } }));
  await page.route(/\/api\/expedientes\/resumen\/(?:\?.*)?$/, (route) => route.fulfill({ json: { anios: [2026], origenes: [], numeracion: { habilitado: true } } }));
  await page.route(/\/api\/expedientes\/pendientes-sigedoc\/(?:\?.*)?$/, (route) => route.fulfill({ json: { count: 0, results: [], next: null } }));
  await page.route('**/api/expedientes/1/', (route) => route.fulfill({ json: { id: 1, numero_formateado: '1/2026', estado_sigedoc: 'PENDIENTE', causante: 'Persona', asunto: 'Nota', auditoria: [], acciones_disponibles: { ver: true, editar: write, anular: role === 'ADMINISTRADOR', registrar_sigedoc: write } } }));
  await page.route(/\/api\/usuarios\/(?:\?.*)?$/, (route) => route.fulfill({ json: { count: 1, results: [{ id: 2, username: 'persona.portal', nombre_visible: 'Ana Pérez', rol: 'CONSULTOR', is_active: true, email: '' }], next: null } }));
}

for (const role of ['ADMINISTRADOR', 'ADMINISTRATIVO', 'CONSULTOR']) {
  test(`${role}: navegación, acciones y acceso directo`, async ({ page }) => {
    await setup(page, role);
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Registro de Expedientes DPA' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Administración · Usuarios' })).toHaveCount(role === 'ADMINISTRADOR' ? 1 : 0);
    await expect(page.getByRole('navigation', { name: 'Secciones' }).getByRole('link', { name: 'Pendientes SIGEDoc' })).toHaveCount(role !== 'CONSULTOR' ? 1 : 0);
    await expect(page.getByRole('button', { name: '+ Nuevo registro' })).toHaveCount(role !== 'CONSULTOR' ? 1 : 0);
    await expect(page.getByRole('button', { name: 'Editar', exact: true })).toHaveCount(role !== 'CONSULTOR' ? 1 : 0);
    await page.goto('/expedientes/1');
    await expect(page.getByRole('heading', { name: 'Expediente N.º 1/2026' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Editar', exact: true })).toHaveCount(0);
    await expect(page.getByRole('button', { name: /Marcar como registrado/ })).toHaveCount(role !== 'CONSULTOR' ? 1 : 0);
    await expect(page.getByRole('button', { name: 'Anular registro', exact: true })).toHaveCount(role === 'ADMINISTRADOR' ? 1 : 0);
    await page.goto('/usuarios');
    if (role === 'ADMINISTRADOR') await expect(page.getByRole('heading', { name: 'Usuarios', exact: true })).toBeVisible();
    else await expect(page.getByRole('alert')).toHaveText('No tenés permisos para acceder a esta sección.');
    await page.goto('/pendientes-sigedoc');
    if (role === 'CONSULTOR') await expect(page.getByRole('alert')).toHaveText('No tenés permisos para acceder a esta sección.');
    else await expect(page.getByRole('heading', { name: 'Pendientes SIGEDoc', exact: true })).toBeVisible();
  });
}

test('administrador crea acceso local y edita rol sin duplicar identidad', async ({ page }) => {
  await setup(page, 'ADMINISTRADOR');
  let created;
  await page.route(/\/api\/usuarios\/(?:\?.*)?$/, async (route) => {
    if (route.request().method() === 'POST') {
      created = route.request().postDataJSON();
      await route.fulfill({ status: 201, json: { id: 3, ...created } });
    } else await route.fulfill({ json: { count: 1, results: [{ id: 2, username: 'persona.portal', nombre_visible: 'Ana Pérez', rol: 'CONSULTOR', is_active: true }], next: null } });
  });
  await page.goto('/usuarios');
  await page.getByRole('button', { name: '+ Nuevo usuario' }).click();
  await page.getByLabel('Usuario de Portal DPA').fill('otra.portal');
  await page.getByRole('button', { name: 'Guardar cambios' }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  expect(created).toMatchObject({ username: 'otra.portal', rol: 'CONSULTOR' });
  expect(created).not.toHaveProperty('password');
  let changed;
  await page.route('**/api/usuarios/2/', (route) => {
    changed = route.request().postDataJSON();
    return route.fulfill({ json: { id: 2, ...changed } });
  });
  await page.getByRole('button', { name: 'Editar', exact: true }).click();
  await page.getByRole('dialog').getByLabel('Rol', { exact: true }).selectOption('ADMINISTRATIVO');
  await page.getByRole('button', { name: 'Guardar cambios' }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  expect(changed.rol).toBe('ADMINISTRATIVO');
  expect(changed).not.toHaveProperty('username');
});

test('desactivar requiere confirmación y muestra rechazo del último administrador', async ({ page }) => {
  await setup(page, 'ADMINISTRADOR');
  let attempts = 0;
  await page.route('**/api/usuarios/2/', (route) => {
    attempts += 1;
    expect(route.request().postDataJSON()).toEqual({ is_active: false });
    return route.fulfill({ status: 400, json: { detail: 'Debe existir al menos un administrador activo en el sistema.' } });
  });
  await page.goto('/usuarios');
  await page.getByRole('button', { name: 'Desactivar', exact: true }).click();
  expect(attempts).toBe(0);
  await expect(page.getByRole('dialog')).toContainText('Sus registros históricos permanecerán asociados');
  await page.getByRole('button', { name: 'Confirmar' }).click();
  await expect(page.locator('[data-sonner-toast][data-type="error"]')).toContainText('Debe existir al menos un administrador activo en el sistema.');
});

test('administrativo edita datos descriptivos conservando número y estado', async ({ page }) => {
  await setup(page, 'ADMINISTRATIVO');
  let changed;
  let persisted = {};
  await page.route(/\/api\/expedientes\/(?:\?.*)?$/, (route) => route.fulfill({ json: { count: 1, next: null, results: [{ id: 1, numero_formateado: '1/2026', causante: 'Persona', asunto: 'Nota', estado_sigedoc: 'PENDIENTE', ...persisted }] } }));
  await page.route('**/api/expedientes/1/', (route) => {
    const record = { id: 1, numero_formateado: '1/2026', causante: 'Persona', asunto: 'Nota', estado_sigedoc: 'PENDIENTE', auditoria: [], acciones_disponibles: { ver: true, editar: true, anular: false, registrar_sigedoc: true }, ...persisted };
    if (route.request().method() === 'PATCH') {
      changed = route.request().postDataJSON();
      persisted = changed;
      return route.fulfill({ json: { ...record, ...changed } });
    }
    return route.fulfill({ json: record });
  });
  await page.goto('/');
  await page.getByRole('button', { name: 'Editar', exact: true }).click();
  await page.getByRole('textbox', { name: /Asunto/ }).fill('Nota corregida');
  await page.getByRole('button', { name: 'Guardar cambios' }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.getByText('Nota corregida', { exact: true })).toBeVisible();
  expect(changed).toEqual({ causante: 'Persona', asunto: 'Nota corregida', tipo: '' });
  await page.getByRole('link', { name: 'Ver', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Expediente N.º 1/2026' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Editar', exact: true })).toHaveCount(0);
});
