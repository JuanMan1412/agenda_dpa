from datetime import datetime, timedelta, timezone
import os
import runpy
from importlib import import_module
from unittest.mock import patch

import jwt
from django.conf import settings
from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from agenda.models import Agenda, ControlNumeracion
from roles.models import Rol

User = get_user_model()


class PortalAuthenticationTests(APITestCase):
    def setUp(self):
        ControlNumeracion.objects.get_or_create(pk=1)

    def token(self, **claims):
        now = datetime.now(timezone.utc)
        payload = {
            'user_id': 1001, 'username': 'empleado.portal', 'nombre_completo': 'Ana Perez',
            'rol': 'ADMINISTRADOR', 'sistemas': [' AGENDA '], 'token_type': 'access',
            'iat': now, 'exp': now + timedelta(minutes=5), 'jti': 'portal-test',
        }
        payload.update(claims)
        return jwt.encode(payload, settings.PORTAL_SIGNING_KEY, algorithm='HS256')

    def exchange(self, token=None):
        return self.client.post(reverse('portal-access'), {'token': token or self.token()}, format='json')

    def login(self):
        response = self.exchange()
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        return response.data

    def test_new_user_is_consultor_with_unusable_password_and_local_identity(self):
        response = self.exchange()
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username='empleado.portal')
        self.assertFalse(user.has_usable_password())
        self.assertEqual(user.portal_user_id, '1001')
        self.assertEqual(response.data['rol'], 'CONSULTOR')
        self.assertNotEqual(user.pk, 1001)
        token = jwt.decode(response.data['access'], settings.PORTAL_SIGNING_KEY, algorithms=['HS256'])
        self.assertEqual(str(token['user_id']), str(user.pk))
        self.assertEqual(token['rol'], 'CONSULTOR')
        self.assertEqual(token['local_system'], 'agenda')

    def test_repeat_access_keeps_local_role_and_does_not_duplicate(self):
        self.exchange()
        user = User.objects.get(portal_user_id='1001')
        user.rol = Rol.objects.get(descripcion='ADMINISTRATIVO')
        user.save()
        response = self.exchange(self.token(nombre_completo='Ana Maria Perez'))
        self.assertEqual(response.data['rol'], 'ADMINISTRATIVO')
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response.data['user']['nombre_completo'], 'Ana Maria Perez')

    def test_invalid_expired_refresh_and_missing_exp_are_401(self):
        invalid_tokens = [
            'malformado', self.token(exp=datetime.now(timezone.utc) - timedelta(seconds=1)),
            self.token(token_type='refresh'), self.token(exp=None),
            jwt.encode({'token_type': 'access', 'exp': 9999999999}, 'another-test-key-with-at-least-32-bytes', algorithm='HS256'),
        ]
        for token in invalid_tokens:
            with self.subTest(token_type='invalid'):
                self.assertEqual(self.exchange(token).status_code, 401)
        self.assertEqual(User.objects.count(), 0)

    def test_refresh_cannot_be_exchanged(self):
        data = self.login()
        self.assertEqual(self.exchange(data['refresh']).status_code, 401)

    def test_token_body_requires_nonempty_string(self):
        for body in [{}, {'token': ''}, {'token': 123}, {'token': []}, {'token': None}]:
            with self.subTest(body=body):
                self.assertEqual(self.client.post(reverse('portal-access'), body, format='json').status_code, 400)

    def test_missing_identity_or_username_is_400(self):
        for claims in [{'user_id': None}, {'user_id': {}}, {'username': None}, {'username': ''}]:
            self.assertEqual(self.exchange(self.token(**claims)).status_code, 400)

    def test_missing_system_is_403(self):
        for systems in [None, ['movil'], {}, []]:
            self.assertEqual(self.exchange(self.token(sistemas=systems)).status_code, 403)

    def test_empty_system_code_is_configuration_error(self):
        with patch.dict(os.environ, {'PORTAL_SYSTEM_CODE': ''}), patch('dotenv.load_dotenv'):
            with self.assertRaises(ImproperlyConfigured):
                runpy.run_path(str(settings.BASE_DIR / 'config' / 'settings.py'))

    def test_empty_signing_key_is_configuration_error(self):
        with patch.dict(os.environ, {'SIGNING_KEY': ''}), patch('dotenv.load_dotenv'):
            with self.assertRaises(ImproperlyConfigured):
                runpy.run_path(str(settings.BASE_DIR / 'config' / 'settings.py'))

    def test_old_bearer_does_not_block_public_exchange(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer vencido')
        self.assertEqual(self.exchange().status_code, 200)

    def test_link_existing_nonprivileged_username(self):
        user = User.objects.create_user(username='empleado.portal', password='local')
        response = self.exchange()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['id'], user.pk)
        user.refresh_from_db()
        self.assertTrue(user.check_password('local'))

    def test_different_portal_id_cannot_take_username(self):
        self.exchange()
        self.assertEqual(self.exchange(self.token(user_id=2002)).status_code, 403)
        self.assertEqual(User.objects.get().portal_user_id, '1001')

    def test_username_collision_is_403_and_rolls_back(self):
        self.exchange()
        User.objects.create_user(username='otra.cuenta')
        response = self.exchange(self.token(username='otra.cuenta'))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(User.objects.get(portal_user_id='1001').username, 'empleado.portal')

    def test_portal_identity_follows_username_change(self):
        self.exchange()
        response = self.exchange(self.token(username='nuevo.username'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, 'nuevo.username')

    def test_unlinked_privileged_account_requires_manual_link(self):
        User.objects.create_superuser(username='empleado.portal', password='local')
        self.assertEqual(self.exchange().status_code, 403)
        self.assertIsNone(User.objects.get().portal_user_id)

    @override_settings(PORTAL_AUTO_ENABLE_USERS=False)
    def test_inactive_account_stays_blocked_without_auto_enable(self):
        self.exchange()
        User.objects.update(is_active=False)
        self.assertEqual(self.exchange().status_code, 403)
        self.assertFalse(User.objects.get().is_active)

    @override_settings(PORTAL_AUTO_ENABLE_USERS=True)
    def test_administrative_deactivation_cannot_be_overridden_by_portal(self):
        self.exchange()
        User.objects.update(is_active=False)
        self.assertEqual(self.exchange().status_code, 403)
        self.assertFalse(User.objects.get().is_active)

    @override_settings(PORTAL_AUTO_ENABLE_USERS=False)
    def test_new_account_is_active_even_without_reactivation(self):
        self.assertEqual(self.exchange().status_code, 200)
        self.assertTrue(User.objects.get().is_active)

    def test_private_endpoints_require_local_jwt(self):
        for route in ['agenda-listar', 'my-permissions']:
            self.assertEqual(self.client.get(reverse(route)).status_code, 401)
        self.assertEqual(self.client.post(reverse('agenda-manual'), {'letra': 'A'}).status_code, 401)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token()}')
        self.assertEqual(self.client.get(reverse('my-permissions')).status_code, 401)

    def test_consultor_can_read_but_cannot_write(self):
        self.login()
        Agenda.objects.create(numero=1, letra='AP', origen='manual', fecha_hora=datetime.now(timezone.utc))
        self.assertEqual(self.client.get(reverse('agenda-listar')).status_code, 200)
        permissions = self.client.get(reverse('my-permissions'))
        self.assertFalse(permissions.data['secciones']['agenda']['escribir'])
        with patch('agenda.views.cargar_manual') as create:
            self.assertEqual(self.client.post(reverse('agenda-manual'), {'letra': 'A'}).status_code, 403)
            create.assert_not_called()

    def test_role_changes_apply_to_existing_access_token(self):
        self.login()
        User.objects.update(rol=Rol.objects.get(descripcion='ADMINISTRATIVO'))
        ControlNumeracion.objects.filter(pk=1).update(habilitado=True)
        self.assertEqual(self.client.post(reverse('agenda-manual'), {'causante': 'Juan', 'asunto': 'Nota'}).status_code, 201)
        User.objects.update(rol=Rol.objects.get(descripcion='CONSULTOR'))
        self.assertEqual(self.client.post(reverse('agenda-manual'), {'letra': 'A'}).status_code, 403)

    def test_inactive_user_rejects_existing_access_and_refresh(self):
        data = self.login()
        User.objects.update(is_active=False)
        self.assertEqual(self.client.get(reverse('my-permissions')).status_code, 401)
        self.assertEqual(self.client.post(reverse('local-token-refresh'), {'refresh': data['refresh']}, format='json').status_code, 401)

    def test_refresh_uses_local_role_and_rejects_central_refresh(self):
        data = self.login()
        User.objects.update(rol=Rol.objects.get(descripcion='ADMINISTRATIVO'))
        response = self.client.post(reverse('local-token-refresh'), {'refresh': data['refresh']}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['rol'], 'ADMINISTRATIVO')
        response = self.client.post(reverse('local-token-refresh'), {'refresh': self.token(token_type='refresh')}, format='json')
        self.assertEqual(response.status_code, 401)

    def test_unknown_role_has_no_permissions(self):
        self.login()
        User.objects.update(rol=Rol.objects.create(descripcion='ROL_AJENO'))
        self.assertEqual(self.client.get(reverse('agenda-listar')).status_code, 403)

    def test_external_service_requires_api_key_not_browser_jwt(self):
        self.login()
        self.assertEqual(self.client.post(reverse('agenda-reservar-externo'), {'letra': 'A'}).status_code, 401)
        with override_settings(AGENDA_API_KEYS={'clave-test': 'expedientes'}):
            ControlNumeracion.objects.filter(pk=1).update(habilitado=True)
            response = self.client.post(reverse('agenda-reservar-externo'), {'causante': 'Juan', 'asunto': 'Nota', 'referencia': 'uuid-1'}, HTTP_X_API_KEY='clave-test')
            self.assertEqual(response.status_code, 201)

    def test_disabled_role_denies_agenda_access(self):
        self.login()
        Rol.objects.filter(descripcion='CONSULTOR').update(estado=False)
        self.assertEqual(self.client.get(reverse('agenda-listar')).status_code, 403)

    def test_response_uses_existing_user_and_role_models(self):
        response = self.exchange()
        user = User.objects.get(portal_user_id='1001')
        self.assertEqual(user._meta.label, 'usuarios.User')
        self.assertEqual(response.data['user']['rol'], user.rol_id)
        self.assertEqual(response.data['user']['rol_detalle'], user.rol.descripcion)


class LegacyUserMigrationTests(APITestCase):
    def test_import_keeps_identity_password_role_and_groups(self):
        password = make_password('local-test-password')
        now = datetime.now(timezone.utc)
        group = Group.objects.create(name='grupo-local')
        with connection.cursor() as cursor:
            cursor.execute('CREATE TABLE auth_user (id INTEGER PRIMARY KEY, username TEXT, password TEXT, email TEXT, first_name TEXT, last_name TEXT, is_active BOOLEAN, is_staff BOOLEAN, is_superuser BOOLEAN, date_joined TEXT, last_login TEXT)')
            cursor.execute('INSERT INTO auth_user VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', [71, 'cuenta.anterior', password, 'user@example.test', 'Ana', 'Perez', False, True, True, now, now])
            cursor.execute('CREATE TABLE portal_accounts_portalprofile (user_id INTEGER, portal_user_id TEXT, rol TEXT, nombre_completo TEXT)')
            cursor.execute('INSERT INTO portal_accounts_portalprofile VALUES (%s,%s,%s,%s)', [71, 'central-123', 'ADMINISTRATIVO', 'Ana Maria Perez'])
            cursor.execute('CREATE TABLE auth_user_groups (user_id INTEGER, group_id INTEGER)')
            cursor.execute('INSERT INTO auth_user_groups VALUES (%s,%s)', [71, group.pk])
        migrate = import_module('usuarios.migrations.0002_import_legacy_users').import_legacy_users
        migrate(apps, connection.schema_editor())
        migrate(apps, connection.schema_editor())
        user = User.objects.get(pk=71)
        self.assertEqual(user.username, 'cuenta.anterior')
        self.assertTrue(user.check_password('local-test-password'))
        self.assertEqual(user.portal_user_id, 'central-123')
        self.assertEqual(user.rol.descripcion, 'ADMINISTRATIVO')
        self.assertEqual(user.nombre_completo, 'Ana Maria Perez')
        self.assertFalse(user.is_active)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.groups.filter(pk=group.pk).exists())
        self.assertEqual(User.objects.count(), 1)


class AdminPagesTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username='admin.test', password='test-password', rol=Rol.objects.get(descripcion='ADMINISTRADOR'))
        self.client.force_login(self.admin)

    def test_user_change_page_and_password_link_work(self):
        user = User.objects.create_user(username='usuario.test', password='test-password')
        response = self.client.get(reverse('admin:usuarios_user_change', args=[user.pk]))
        self.assertEqual(response.status_code, 200)
        password_url = reverse('admin:auth_user_password_change', args=[user.pk])
        self.assertContains(response, password_url)
        self.assertEqual(self.client.get(password_url).status_code, 200)

    def test_agenda_is_available_in_admin(self):
        entry = Agenda.objects.create(numero=1, letra='AP', origen='manual', fecha_hora=datetime.now(timezone.utc))
        response = self.client.get(reverse('admin:agenda_agenda_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, entry.numero_formateado)
        self.assertEqual(self.client.get(reverse('admin:agenda_agenda_change', args=[entry.pk])).status_code, 200)
