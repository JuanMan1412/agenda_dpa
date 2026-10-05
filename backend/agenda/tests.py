from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone as dt_timezone
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection, connections, DatabaseError, transaction
from django.test import TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from roles.models import Rol
from .models import Agenda, AuditoriaExpediente, ControlNumeracion, CorrelativoAnual
from .services import cargar_manual, reservar_automatico

User = get_user_model()
BODY = {'causante': 'Juan Perez', 'asunto': 'Linea de Ribera', 'tipo': 'LINEA_RIBERA'}
KEYS = {'test-service-key': {'sistema': 'TRAMITES', 'permisos': ['reservar', 'consultar']},
        'other-key': {'sistema': 'OBRAS', 'permisos': ['reservar', 'consultar']},
        'read-key': {'sistema': 'TRAMITES', 'permisos': ['consultar']}}


@override_settings(EXPEDIENTES_API_KEYS=KEYS)
class RegistroTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='mesa.test', rol=Rol.objects.get(descripcion='ADMINISTRATIVO'))
        self.client.force_authenticate(user=self.user)
        ControlNumeracion.objects.filter(pk=1).update(habilitado=True)

    def manual(self, **values):
        return self.client.post(reverse('expediente-manual'), {**BODY, **values}, format='json')

    def reserve(self, reference='uuid-abc', key='test-service-key', **values):
        self.client.force_authenticate(user=None)
        return self.client.post(reverse('integracion-reservar'), {**BODY, 'referencia': reference, **values}, format='json', HTTP_X_API_KEY=key)

    def test_manual_and_services_share_counter(self):
        first = self.manual()
        second = self.reserve()
        self.client.force_authenticate(user=self.user)
        third = self.manual()
        self.assertEqual([first.status_code, second.status_code, third.status_code], [201]*3)
        self.assertEqual([first.data['numero'], second.data['numero'], third.data['numero']], [1, 2, 3])
        self.assertEqual(first.data['estado_sigedoc'], 'PENDIENTE')
        self.assertEqual(second.data['sistema_origen'], 'TRAMITES')
        self.assertEqual(first.data['origen'], 'MESA_ENTRADA')
        self.assertEqual(AuditoriaExpediente.objects.filter(accion='CREAR_REGISTRO').count(), 3)

    def test_retry_does_not_consume_counter_or_repeat_audit(self):
        first, retry = self.reserve(), self.reserve()
        self.assertEqual(first.data['id'], retry.data['id'])
        self.assertEqual(retry.status_code, 200)
        self.assertEqual(CorrelativoAnual.objects.get(anio=timezone.localdate().year).ultimo_numero, 1)
        self.assertEqual(AuditoriaExpediente.objects.count(), 1)
        self.assertEqual(self.reserve(asunto='Otra cosa').status_code, 409)

    def test_manual_idempotency_prevents_double_click(self):
        for _ in range(2):
            result = self.client.post(reverse('expediente-manual'), BODY, format='json', HTTP_IDEMPOTENCY_KEY='manual-uuid')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(Agenda.objects.count(), 1)

    def test_retry_cross_year_keeps_original_expediente(self):
        with patch('agenda.services.timezone.now', return_value=datetime(2026, 12, 31, 18, tzinfo=dt_timezone.utc)):
            first = self.reserve()
        with patch('agenda.services.timezone.now', return_value=datetime(2027, 1, 1, 18, tzinfo=dt_timezone.utc)):
            second = self.reserve()
            third = self.reserve(reference='new-year')
        self.assertEqual((first.data['numero'], first.data['anio']), (1, 2026))
        self.assertEqual((second.data['numero'], second.data['anio']), (1, 2026))
        self.assertEqual((third.data['numero'], third.data['anio']), (1, 2027))

    def test_year_boundary_and_argentina_time(self):
        CorrelativoAnual.objects.update_or_create(anio=2026, defaults={'ultimo_numero': 15235})
        with patch('agenda.services.timezone.now', return_value=datetime(2027, 1, 1, 1, tzinfo=dt_timezone.utc)):
            last = self.manual()
        with patch('agenda.services.timezone.now', return_value=datetime(2027, 1, 1, 4, tzinfo=dt_timezone.utc)):
            first = self.manual()
            second = self.manual()
        self.assertEqual((last.data['numero'], last.data['anio']), (15236, 2026))
        self.assertEqual((first.data['numero'], first.data['anio']), (1, 2027))
        self.assertEqual((second.data['numero'], second.data['anio']), (2, 2027))

    def test_sigedoc_confirmation_records_actor_once(self):
        item = self.manual().data
        url = reverse('expediente-sigedoc', args=[item['id']])
        self.assertEqual(self.client.post(url, {'confirmar': False}).status_code, 400)
        response = self.client.post(url, {'confirmar': True})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['estado_sigedoc'], 'REGISTRADO')
        self.assertEqual(response.data['registrado_sigedoc_por'], self.user.pk)
        self.assertIsNotNone(response.data['fecha_registro_sigedoc'])
        self.assertEqual(response.data['numero'], item['numero'])
        self.client.post(url, {'confirmar': True})
        self.assertEqual(AuditoriaExpediente.objects.filter(accion='REGISTRAR_SIGEDOC').count(), 1)

    def test_annul_requires_admin_and_reason_number_not_reused(self):
        item = self.manual().data
        url = reverse('expediente-anular', args=[item['id']])
        self.assertEqual(self.client.post(url, {'motivo': 'Error'}).status_code, 403)
        self.user.rol = Rol.objects.get(descripcion='ADMINISTRADOR')
        self.user.save()
        self.assertEqual(self.client.post(url, {'motivo': ''}).status_code, 400)
        response = self.client.post(url, {'motivo': 'Presentacion duplicada'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['anulado'])
        self.assertEqual(response.data['anulado_por'], self.user.pk)
        self.assertEqual(self.manual().data['numero'], 2)
        self.assertEqual(Agenda.objects.count(), 2)
        self.assertEqual(self.client.post(reverse('expediente-sigedoc', args=[item['id']]), {'confirmar': True}).status_code, 409)
        self.assertEqual(self.client.delete(reverse('expediente-detalle', args=[item['id']])).status_code, 405)

    def test_consultor_cannot_create_mark_or_annul(self):
        item = self.manual().data
        self.user.rol = Rol.objects.get(descripcion='CONSULTOR')
        self.user.save()
        self.assertEqual(self.manual().status_code, 403)
        self.assertEqual(self.client.post(reverse('expediente-sigedoc', args=[item['id']]), {'confirmar': True}).status_code, 403)
        self.assertEqual(self.client.post(reverse('expediente-anular', args=[item['id']]), {'motivo': 'Error'}).status_code, 403)
        self.assertEqual(self.client.get(reverse('expediente-detalle', args=[item['id']])).status_code, 200)

    def test_service_security_identity_permissions_and_own_records(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.post(reverse('integracion-reservar'), BODY).status_code, 401)
        self.assertEqual(self.reserve(key='read-key').status_code, 403)
        self.assertEqual(self.reserve(sistema='OBRAS').status_code, 403)
        self.assertEqual(self.reserve(numero=1234).status_code, 400)
        self.assertEqual(self.reserve(anio=2027).status_code, 400)
        first = self.reserve()
        own = reverse('integracion-detalle', args=[first.data['id']])
        self.assertEqual(self.client.get(own, HTTP_X_API_KEY='test-service-key').status_code, 200)
        self.assertEqual(self.client.get(own, HTTP_X_API_KEY='other-key').status_code, 404)
        self.assertEqual(self.client.post(reverse('expediente-sigedoc', args=[first.data['id']]), {'confirmar': True}, HTTP_X_API_KEY='test-service-key').status_code, 401)
        self.assertEqual(self.client.get(reverse('integracion-referencia'), {'referencia': 'uuid-abc'}, HTTP_X_API_KEY='test-service-key').status_code, 200)

    def test_search_filters_and_old_years(self):
        first = self.manual().data
        self.manual(causante='Municipalidad', asunto='Nota administrativa')
        base = reverse('expediente-listar')
        self.assertEqual(self.client.get(base, {'q': str(first['numero'])}).data['count'], 1)
        self.assertEqual(self.client.get(base, {'q': first['numero_formateado']}).data['count'], 1)
        self.assertEqual(self.client.get(base, {'q': 'municipalidad'}).data['count'], 1)
        self.assertEqual(self.client.get(base, {'estado': 'PENDIENTE'}).data['count'], 2)
        self.assertEqual(self.client.get(base, {'estado': 'REGISTRADO'}).data['count'], 0)
        self.assertEqual(self.client.get(base, {'anio': 'invalid'}).status_code, 400)
        self.assertEqual(self.client.get(base, {'origen': 'MESA_ENTRADA', 'hoy': 'true'}).data['count'], 2)
        summary = self.client.get(reverse('expediente-resumen')).data
        self.assertEqual(summary['pendientes'], 2)
        self.assertIn(timezone.localdate().year, summary['anios'])
        self.assertEqual(self.client.get(reverse('agenda-listar')).status_code, 200)

    def test_pending_oldest_first_excludes_annulled(self):
        first = self.manual().data
        second = self.manual().data
        response = self.client.get(reverse('expediente-listar'), {'estado': 'PENDIENTE', 'orden': 'fecha_asc'})
        self.assertEqual([r['id'] for r in response.data['results']], [first['id'], second['id']])

    def test_manual_cannot_choose_number_year_or_initial_status(self):
        for values in [{'numero': 15235}, {'anio': 2027}, {'estado_sigedoc': 'REGISTRADO'}, {'origen': 'SISTEMA_TRAMITES'}]:
            self.assertEqual(self.manual(**values).status_code, 400)
        self.assertEqual(Agenda.objects.count(), 0)

    def test_historical_records_with_missing_metadata_remain_visible(self):
        historical = Agenda.objects.create(numero=42, anio=2025, letra='AP', origen='MESA_ENTRADA', fecha_hora=datetime(2025, 8, 1, 12, tzinfo=dt_timezone.utc))
        response = self.client.get(reverse('expediente-listar'), {'anio': 2025})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['numero_formateado'], '42/2025')
        self.assertEqual(response.data['results'][0]['letra'], 'AP')
        self.assertEqual(self.client.get(reverse('expediente-detalle', args=[historical.pk])).status_code, 200)

    def test_allocation_disabled_until_explicit_confirmation(self):
        ControlNumeracion.objects.update(habilitado=False)
        self.assertEqual(self.manual().status_code, 409)
        self.assertEqual(self.reserve().status_code, 409)
        self.assertEqual(Agenda.objects.count(), 0)
        self.assertEqual(CorrelativoAnual.objects.get(anio=timezone.localdate().year).ultimo_numero, 0)
        call_command('confirmar_correlativo', verbosity=0)
        self.assertFalse(ControlNumeracion.objects.get(pk=1).habilitado)

    def test_confirmation_cannot_move_back_and_records_audit(self):
        self.user.rol = Rol.objects.get(descripcion='ADMINISTRADOR')
        self.user.save()
        counter = CorrelativoAnual.objects.get(anio=timezone.localdate().year)
        counter.ultimo_numero = 100
        counter.save()
        with self.assertRaises(CommandError):
            call_command('confirmar_correlativo', anio=counter.anio, ultimo_numero_libro=99, usuario=self.user.username, confirmar=True)
        call_command('confirmar_correlativo', anio=counter.anio, ultimo_numero_libro=15234, usuario=self.user.username, confirmar=True)
        self.assertEqual(self.manual().data['numero'], 15235)
        self.assertTrue(AuditoriaExpediente.objects.filter(accion='CONFIRMAR_CORRELATIVO').exists())

    def test_failure_rolls_back_counter_record_and_audit(self):
        with patch('agenda.services.AuditoriaExpediente.objects.create', side_effect=RuntimeError('failure')):
            with self.assertRaises(RuntimeError): cargar_manual(usuario=self.user, **BODY)
        self.assertEqual(Agenda.objects.count(), 0)
        self.assertEqual(CorrelativoAnual.objects.get(anio=timezone.localdate().year).ultimo_numero, 0)

    def test_retry_keeps_annulled_original(self):
        original = self.reserve()
        self.client.force_authenticate(user=self.user)
        self.user.rol = Rol.objects.get(descripcion='ADMINISTRADOR')
        self.user.save()
        self.client.post(reverse('expediente-anular', args=[original.data['id']]), {'motivo': 'Error'})
        retry = self.reserve()
        self.assertEqual(retry.data['id'], original.data['id'])
        self.assertTrue(retry.data['anulado'])


@skipUnless(connection.vendor == 'postgresql', 'Estas pruebas requieren PostgreSQL real.')
class ConcurrenciaPostgresTests(TransactionTestCase):
    def setUp(self):
        ControlNumeracion.objects.update_or_create(pk=1, defaults={'habilitado': True})

    def run_parallel(self, tasks):
        barrier = Barrier(len(tasks))
        def run(task):
            connections.close_all()
            try:
                barrier.wait(timeout=10)
                return task()
            finally: connections.close_all()
        with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
            return list(executor.map(run, tasks))

    def test_simultaneous_manual_and_system_never_duplicate(self):
        tasks = [lambda: cargar_manual(**BODY), lambda: reservar_automatico(sistema='TRAMITES', referencia_externa='ref1', **BODY), lambda: cargar_manual(**BODY)]
        results = self.run_parallel(tasks)
        self.assertEqual(sorted(item[0].numero for item in results), [1, 2, 3])
        self.assertEqual(Agenda.objects.count(), 3)

    def test_simultaneous_retry_consumes_only_one_number(self):
        task = lambda: reservar_automatico(sistema='TRAMITES', referencia_externa='same-ref', **BODY)
        results = self.run_parallel([task, task, task])
        self.assertEqual(len({item[0].pk for item in results}), 1)
        self.assertEqual(sum(item[1] for item in results), 1)
        self.assertEqual(Agenda.objects.count(), 1)
        self.assertEqual(AuditoriaExpediente.objects.count(), 1)
        self.assertEqual(CorrelativoAnual.objects.get().ultimo_numero, 1)

    def test_first_requests_new_year_share_first_counter(self):
        task = lambda: cargar_manual(**BODY)
        with patch('agenda.services.timezone.now', return_value=datetime(2027, 1, 1, 18, tzinfo=dt_timezone.utc)):
            results = self.run_parallel([task, task])
        self.assertEqual(sorted((item[0].anio, item[0].numero) for item in results), [(2027, 1), (2027, 2)])

    def test_database_prevents_deleting_or_changing_number(self):
        item, _ = cargar_manual(**BODY)
        with self.assertRaises(DatabaseError), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute('DELETE FROM agenda WHERE id=%s', [item.pk])
        with self.assertRaises(DatabaseError), transaction.atomic():
            Agenda.objects.filter(pk=item.pk).update(numero=9999)
        self.assertTrue(Agenda.objects.filter(pk=item.pk, numero=1).exists())
