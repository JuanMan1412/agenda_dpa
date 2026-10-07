from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from agenda.services import confirmar_numeracion, estado_numeracion


class Command(BaseCommand):
    help = 'Muestra el correlativo; habilita altas solo con confirmacion explicita del libro fisico.'

    def add_arguments(self, parser):
        parser.add_argument('--anio', type=int)
        parser.add_argument('--ultimo-numero-libro', type=int)
        parser.add_argument('--usuario')
        parser.add_argument('--confirmar', action='store_true')

    def handle(self, *args, **options):
        state = estado_numeracion()
        year = state['anio']
        self.stdout.write(f"Anio: {year}; ultimo en base: {state['ultimo_numero_base']}; ultimo consumido: {state['ultimo_numero_consumido']}; proximo: {state['proximo_numero']}; habilitado: {state['habilitado']}")
        if not options['confirmar']:
            self.stdout.write('Solo consulta. Comparar con el libro fisico antes de confirmar.')
            return
        User = get_user_model()
        user = User.objects.filter(username=options['usuario'], is_active=True).select_related('rol').first()
        try:
            next_number = confirmar_numeracion(anio=options['anio'],
                ultimo_numero_libro=options['ultimo_numero_libro'], usuario=user)
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f'Asignaciones habilitadas. Proximo expediente: {next_number}/{year}.'))
