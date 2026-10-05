from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from agenda.models import AuditoriaExpediente, ControlNumeracion, CorrelativoAnual
from agenda.services import _lock, estado_numeracion


class Command(BaseCommand):
    help = 'Muestra el correlativo; habilita altas solo con confirmacion explicita del libro fisico.'

    def add_arguments(self, parser):
        parser.add_argument('--anio', type=int)
        parser.add_argument('--ultimo-numero-libro', type=int)
        parser.add_argument('--usuario')
        parser.add_argument('--confirmar', action='store_true')

    @transaction.atomic
    def handle(self, *args, **options):
        state = estado_numeracion()
        year = state['anio']
        self.stdout.write(f"Anio: {year}; ultimo en base: {state['ultimo_numero_base']}; ultimo consumido: {state['ultimo_numero_consumido']}; proximo: {state['proximo_numero']}; habilitado: {state['habilitado']}")
        if not options['confirmar']:
            self.stdout.write('Solo consulta. Comparar con el libro fisico antes de confirmar.')
            return
        if options['anio'] != year:
            raise CommandError('Indicar --anio con el anio actual verificado.')
        last = options['ultimo_numero_libro']
        if last is None or last < 0:
            raise CommandError('Indicar --ultimo-numero-libro con el ultimo numero real del libro.')
        User = get_user_model()
        user = User.objects.filter(username=options['usuario'], is_active=True).select_related('rol').first()
        if not user or not (user.is_superuser or (user.rol and user.rol.estado and user.rol.descripcion == 'ADMINISTRADOR')):
            raise CommandError('Indicar --usuario con un administrador local activo.')
        _lock(f'correlativo-anual:{year}')
        counter, _ = CorrelativoAnual.objects.get_or_create(anio=year)
        counter = CorrelativoAnual.objects.select_for_update().get(pk=year)
        if last < max(counter.ultimo_numero, state['ultimo_numero_consumido']):
            raise CommandError('El libro informado es inferior al piso consumido. Revisar la diferencia; no se reutilizaran numeros.')
        before = counter.ultimo_numero
        counter.ultimo_numero = last
        counter.save(update_fields=['ultimo_numero'])
        control, _ = ControlNumeracion.objects.get_or_create(pk=1)
        control.habilitado = True
        control.anio_validado = year
        control.ultimo_numero_libro = last
        control.confirmado_por = user
        control.fecha_confirmacion = timezone.now()
        control.save()
        AuditoriaExpediente.objects.create(usuario=user, accion='CONFIRMAR_CORRELATIVO',
            datos={'anio': year, 'ultimo_anterior': before, 'ultimo_libro': last, 'proximo': last + 1},
            motivo='Comparacion explicita con el libro fisico de Mesa de Entrada.')
        self.stdout.write(self.style.SUCCESS(f'Asignaciones habilitadas. Proximo expediente: {last + 1}/{year}.'))
