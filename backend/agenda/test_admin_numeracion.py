from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from roles.models import Rol
from .models import AuditoriaExpediente, ControlNumeracion, CorrelativoAnual
from .services import cargar_manual


class NumeracionAdminTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='numeracion.admin',
            is_staff=True, rol=Rol.objects.get(descripcion='ADMINISTRADOR'))
        self.client.force_login(self.user)
        self.url = reverse('admin:agenda_controlnumeracion_changelist')
        self.year = timezone.localdate().year

    def post(self, **values):
        return self.client.post(self.url, {'anio': self.year, 'ultimo_numero_libro': 15234,
            'confirmar': 'on', **values})

    def test_visible_without_existing_control_and_read_does_not_enable(self):
        ControlNumeracion.objects.all().delete()
        self.assertContains(self.client.get(reverse('admin:index')), self.url)
        self.assertContains(self.client.get(self.url), 'Último número usado')
        self.assertFalse(ControlNumeracion.objects.exists())

    def test_confirm_enables_audits_and_assigns_next_number(self):
        self.assertEqual(self.post().status_code, 302)
        control = ControlNumeracion.objects.get(pk=1)
        self.assertTrue(control.habilitado)
        self.assertEqual(control.confirmado_por, self.user)
        audit = AuditoriaExpediente.objects.get(accion='CONFIRMAR_CORRELATIVO')
        self.assertEqual(audit.datos['proximo'], 15235)
        record, _ = cargar_manual(usuario=self.user, causante='Persona', asunto='Nota')
        self.assertEqual(record.numero, 15235)

    def test_invalid_confirmation_does_not_mutate(self):
        CorrelativoAnual.objects.update_or_create(anio=self.year, defaults={'ultimo_numero': 100})
        for values in ({'ultimo_numero_libro': 99}, {'confirmar': ''}, {'anio': self.year - 1},
                       {'ultimo_numero_libro': -1}):
            self.assertEqual(self.post(**values).status_code, 200)
            self.assertEqual(CorrelativoAnual.objects.get(pk=self.year).ultimo_numero, 100)
            self.assertFalse(AuditoriaExpediente.objects.filter(accion='CONFIRMAR_CORRELATIVO').exists())

    def test_other_roles_and_inactive_role_cannot_confirm(self):
        for role in ('ADMINISTRATIVO', 'CONSULTOR'):
            self.user.rol = Rol.objects.get(descripcion=role)
            self.user.save()
            self.assertNotEqual(self.post().status_code, 200)
            self.assertFalse(AuditoriaExpediente.objects.filter(accion='CONFIRMAR_CORRELATIVO').exists())
        self.user.rol = Rol.objects.get(descripcion='ADMINISTRADOR')
        self.user.rol.estado = False
        self.user.rol.save()
        self.user.save()
        self.assertNotEqual(self.post().status_code, 200)
        self.assertFalse(AuditoriaExpediente.objects.filter(accion='CONFIRMAR_CORRELATIVO').exists())

    def test_csrf_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(self.url, {'anio': self.year, 'ultimo_numero_libro': 100,
            'confirmar': 'on'}).status_code, 403)
