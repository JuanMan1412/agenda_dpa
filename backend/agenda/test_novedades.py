from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from roles.models import Rol
from .models import Agenda


class NovedadesTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='novedades',
            rol=Rol.objects.get(descripcion='CONSULTOR'))
        self.client.force_authenticate(self.user)
        self.url = reverse('expediente-novedades')

    def record(self, numero, sistema='TRAMITES'):
        return Agenda.objects.create(numero=numero, origen=f'SISTEMA_{sistema}' if sistema else 'MESA_ENTRADA',
            sistema_origen=sistema, causante='Persona', asunto='Nota')

    def test_baseline_excludes_history_and_returns_only_new_external_reservations(self):
        old = self.record(1)
        baseline = self.client.get(self.url).data
        self.assertEqual(baseline, {'cursor': old.id, 'results': []})
        self.record(2, sistema='')
        new = self.record(3)
        response = self.client.get(self.url, {'despues_id': baseline['cursor']}).data
        self.assertEqual([row['id'] for row in response['results']], [new.id])
        self.assertEqual(response['cursor'], new.id)
        self.assertEqual(self.client.get(self.url, {'despues_id': new.id}).data['results'], [])

    def test_cursor_validated_and_access_requires_local_permissions(self):
        for value in ('bad', '-1'):
            self.assertEqual(self.client.get(self.url, {'despues_id': value}).status_code, 400)
        self.user.rol = None
        self.user.save()
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_batches_do_not_skip_reservations(self):
        for number in range(1, 103):
            self.record(number)
        first = self.client.get(self.url, {'despues_id': 0}).data
        second = self.client.get(self.url, {'despues_id': first['cursor']}).data
        self.assertEqual(len(first['results']), 100)
        self.assertEqual(len(second['results']), 2)
