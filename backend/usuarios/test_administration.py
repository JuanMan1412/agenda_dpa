from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from agenda.models import Agenda, AuditoriaExpediente, ControlNumeracion, CorrelativoAnual
from roles.models import Rol
from .models import AuditoriaUsuario

User = get_user_model()


class AdministrationTests(APITestCase):
    def setUp(self):
        self.roles = {name: Rol.objects.get(descripcion=name) for name in ('ADMINISTRADOR', 'ADMINISTRATIVO', 'CONSULTOR')}
        self.admin = User.objects.create_user(username='admin', rol=self.roles['ADMINISTRADOR'])
        self.worker = User.objects.create_user(username='worker', rol=self.roles['ADMINISTRATIVO'])
        self.reader = User.objects.create_user(username='reader', rol=self.roles['CONSULTOR'])
        self.client.force_authenticate(self.admin)
        ControlNumeracion.objects.update_or_create(pk=1, defaults={'habilitado': True})
        self.record = Agenda.objects.create(numero=1, causante='Persona', asunto='Nota', origen='MESA_ENTRADA', creado_por=self.worker)
        CorrelativoAnual.objects.update_or_create(anio=self.record.anio, defaults={'ultimo_numero': 1})

    def url(self, user):
        return f'/api/usuarios/{user.pk}/'

    def test_admin_creates_local_access_with_unusable_password(self):
        result = self.client.post('/api/usuarios/', {'username': 'portal.person', 'rol': 'CONSULTOR', 'is_active': True}, format='json')
        self.assertEqual(result.status_code, 201, result.data)
        user = User.objects.get(pk=result.data['id'])
        self.assertFalse(user.has_usable_password())
        self.assertIsNone(user.portal_user_id)
        self.assertTrue(AuditoriaUsuario.objects.filter(usuario=user, accion='USUARIO_CREADO').exists())

    def test_admin_edits_role_email_and_state_with_audit(self):
        result = self.client.patch(self.url(self.worker), {'rol': 'CONSULTOR', 'email': 'user@example.test', 'is_active': False}, format='json')
        self.assertEqual(result.status_code, 200)
        self.worker.refresh_from_db()
        self.assertFalse(self.worker.is_active)
        self.assertEqual(self.worker.rol.descripcion, 'CONSULTOR')
        self.assertEqual(Agenda.objects.get(pk=self.record.pk).creado_por, self.worker)
        self.assertTrue(AuditoriaUsuario.objects.filter(accion='ROL_CAMBIADO', datos__rol_anterior='ADMINISTRATIVO', datos__rol_nuevo='CONSULTOR').exists())
        self.assertTrue(AuditoriaUsuario.objects.filter(accion='USUARIO_DESACTIVADO').exists())
        self.assertEqual(self.client.patch(self.url(self.worker), {'is_active': True}, format='json').status_code, 200)
        self.assertTrue(AuditoriaUsuario.objects.filter(accion='USUARIO_ACTIVADO').exists())

    def test_last_admin_cannot_be_demoted_deactivated_deleted(self):
        for body in ({'rol': 'CONSULTOR'}, {'rol': 'ADMINISTRATIVO'}, {'is_active': False}):
            response = self.client.patch(self.url(self.admin), body, format='json')
            self.assertEqual(response.status_code, 400)
            self.assertIn('administrador activo', str(response.data))
        self.assertEqual(self.client.delete(self.url(self.admin)).status_code, 400)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
        self.assertEqual(self.admin.rol.descripcion, 'ADMINISTRADOR')

    def test_another_active_admin_allows_role_change(self):
        User.objects.create_user(username='second', rol=self.roles['ADMINISTRADOR'])
        self.assertEqual(self.client.patch(self.url(self.admin), {'rol': 'CONSULTOR'}, format='json').status_code, 200)

    def test_self_deletion_is_rejected_even_with_another_admin(self):
        User.objects.create_user(username='second', rol=self.roles['ADMINISTRADOR'])
        self.assertEqual(self.client.delete(self.url(self.admin)).status_code, 400)

    def test_audit_actor_and_password_history_prevent_deletion(self):
        from .models import PasswordHistory
        audit_actor = User.objects.create_user(username='old-admin', rol=self.roles['ADMINISTRADOR'])
        AuditoriaUsuario.objects.create(actor=audit_actor, usuario=self.reader, usuario_id_historico=self.reader.pk,
            username_historico=self.reader.username, accion='USUARIO_EDITADO')
        self.assertEqual(self.client.delete(self.url(audit_actor)).status_code, 400)
        PasswordHistory.objects.create(user=self.reader, password='historical-hash')
        self.assertEqual(self.client.delete(self.url(self.reader)).status_code, 400)

    def test_admin_form_protects_last_admin_and_admin_pages_require_role(self):
        from .forms import UserChangeForm
        from .admin.usuario import UsuarioAdmin
        from django.contrib.admin import site
        from django.test import RequestFactory
        for values in ({'rol': self.roles['CONSULTOR'].pk, 'is_active': True},
                       {'rol': self.roles['ADMINISTRADOR'].pk, 'is_active': False}):
            form = UserChangeForm(data={'username': self.admin.username, **values}, instance=User.objects.get(pk=self.admin.pk))
            self.assertFalse(form.is_valid())
            self.assertIn('administrador activo', str(form.non_field_errors()))
        request = RequestFactory().get('/admin/usuarios/user/')
        request.user = self.reader
        self.assertFalse(UsuarioAdmin(User, site).has_view_permission(request))

    def test_django_admin_rejects_other_roles_even_if_staff_superuser(self):
        from django.contrib.admin import site
        from django.test import RequestFactory
        request = RequestFactory().get('/admin/')
        for user in (self.worker, self.reader):
            user.is_staff = user.is_superuser = True
            user.save()
            request.user = user
            self.assertFalse(site.has_permission(request))
        self.admin.is_staff = True
        self.admin.save()
        request.user = self.admin
        self.assertTrue(site.has_permission(request))

    def test_deletion_preserves_history_and_allows_unused_user(self):
        self.assertEqual(self.client.delete(self.url(self.worker)).status_code, 400)
        user_id = self.reader.pk
        self.assertEqual(self.client.delete(self.url(self.reader)).status_code, 204)
        audit = AuditoriaUsuario.objects.get(accion='USUARIO_ELIMINADO')
        self.assertIsNone(audit.usuario)
        self.assertEqual(audit.usuario_id_historico, user_id)
        self.assertEqual(audit.username_historico, 'reader')

    def test_no_identity_or_privilege_injection(self):
        for body in ({'username': 'renamed'}, {'portal_user_id': '1'}, {'is_superuser': True}, {'rol': 'MESA_ENTRADA'}):
            self.assertEqual(self.client.patch(self.url(self.worker), body, format='json').status_code, 400)

    def test_users_api_forbidden_to_other_roles(self):
        for user in (self.worker, self.reader):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get('/api/usuarios/').status_code, 403)
            self.assertEqual(self.client.post('/api/usuarios/', {'username': 'x', 'rol': 'CONSULTOR'}).status_code, 403)
            for method in ('get', 'patch', 'put', 'delete'):
                self.assertEqual(getattr(self.client, method)(self.url(self.admin)).status_code, 403)

    def test_role_matrix_for_records_and_pending(self):
        for user in (self.admin, self.worker, self.reader):
            self.client.force_authenticate(user)
            write = user != self.reader
            self.assertEqual(self.client.get('/api/expedientes/').status_code, 200)
            detail_url = f'/api/expedientes/{self.record.pk}/'
            detail = self.client.get(detail_url)
            self.assertEqual(detail.status_code, 200)
            self.assertEqual(detail.data['acciones_disponibles']['editar'], write)
            self.assertEqual(self.client.get('/api/expedientes/pendientes-sigedoc/').status_code, 200 if write else 403)
            self.assertEqual(self.client.patch(detail_url, {'asunto': 'Corregido'}, format='json').status_code, 200 if write else 403)
            self.assertEqual(self.client.put(detail_url, {'causante': 'Persona', 'asunto': 'Nota'}, format='json').status_code, 200 if write else 403)
            self.assertEqual(self.client.post('/api/expedientes/', {'causante': 'Nueva persona', 'asunto': 'Otra nota'}, format='json').status_code, 201 if write else 403)
            self.assertEqual(self.client.post(detail_url + 'registrar-sigedoc/', {'confirmar': True}, format='json').status_code, 200 if write else 403)
        self.assertEqual(self.client.delete(detail_url).status_code, 403)
        self.assertEqual(self.client.post(detail_url + 'anular/', {'motivo': 'Error'}, format='json').status_code, 403)
        self.client.force_authenticate(self.worker)
        self.assertEqual(self.client.post(detail_url + 'anular/', {'motivo': 'Error'}, format='json').status_code, 403)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.post(detail_url + 'anular/', {'motivo': 'Error'}, format='json').status_code, 200)
        self.assertTrue(AuditoriaExpediente.objects.filter(accion='EDITAR_REGISTRO').exists())
        self.assertEqual(self.client.patch(detail_url, {'asunto': 'No'}, format='json').status_code, 409)

    def test_edit_preserves_number_state_and_rejects_protected_fields(self):
        url = f'/api/expedientes/{self.record.pk}/'
        for field in ('numero', 'anio', 'origen', 'estado_sigedoc', 'creado_por'):
            self.assertEqual(self.client.patch(url, {field: 'x'}, format='json').status_code, 400)
        self.assertEqual(self.client.patch(url, {'asunto': 'Actualizado'}, format='json').status_code, 200)
        self.record.refresh_from_db()
        self.assertEqual(self.record.numero, 1)
        self.assertEqual(self.record.estado_sigedoc, 'PENDIENTE')

    def test_search_and_server_pagination(self):
        response = self.client.get('/api/usuarios/', {'rol': 'ADMINISTRATIVO', 'is_active': 'true', 'q': 'worker', 'page_size': 1})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.worker.pk)
        response = self.client.get('/api/usuarios/', {'page_size': 1})
        self.assertEqual(len(response.data['results']), 1)
        self.assertIsNotNone(response.data['next'])

    def test_deactivation_preserves_sigedoc_annulment_and_audit(self):
        self.record.registrado_sigedoc_por = self.worker
        self.record.anulado_por = self.worker
        self.record.save()
        history = AuditoriaExpediente.objects.create(registro=self.record, usuario=self.worker, accion='REGISTRAR_SIGEDOC')
        self.assertEqual(self.client.patch(self.url(self.worker), {'is_active': False}, format='json').status_code, 200)
        self.record.refresh_from_db()
        history.refresh_from_db()
        self.assertEqual(self.record.registrado_sigedoc_por_id, self.worker.pk)
        self.assertEqual(self.record.anulado_por_id, self.worker.pk)
        self.assertEqual(history.usuario_id, self.worker.pk)
        self.assertEqual(self.client.delete(self.url(self.worker)).status_code, 400)
