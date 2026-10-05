import hashlib
from django.db import connection, transaction
from django.db.models import Max, Q
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError
from .models import Agenda, AuditoriaExpediente, ControlNumeracion, CorrelativoAnual


class NumeracionNoHabilitada(APIException):
    status_code = 409
    default_detail = 'Las asignaciones estan bloqueadas hasta confirmar el correlativo con el libro fisico.'
    default_code = 'numeracion_no_habilitada'


class ConflictoRegistro(APIException):
    status_code = 409
    default_code = 'conflicto_registro'


def _lock(key):
    # El bloqueo incluye la primera solicitud del anio o referencia, aun sin fila.
    if connection.vendor == 'postgresql':
        digest = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], 'big', signed=True)
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_advisory_xact_lock(%s)', [digest])


def estado_numeracion():
    anio = timezone.localdate().year
    last = Agenda.objects.filter(anio=anio).aggregate(value=Max('numero'))['value']
    counter = CorrelativoAnual.objects.filter(anio=anio).first()
    ultimo = max(last or 0, counter.ultimo_numero if counter else 0)
    control = ControlNumeracion.objects.filter(pk=1).first()
    return {'anio': anio, 'ultimo_numero_base': last, 'ultimo_numero_consumido': ultimo,
            'proximo_numero': ultimo + 1, 'habilitado': bool(control and control.habilitado)}


@transaction.atomic
def crear_registro(*, causante, asunto, tipo='', letra='', usuario=None, sistema='', referencia=None, idempotencia=None):
    # Orden global estable para locks multiples evita deadlocks entre referencias.
    keys = []
    if referencia: keys.append(f'referencia:{sistema}:{referencia}')
    if idempotencia: keys.append(f'idempotencia:{sistema}:{idempotencia}')
    for key in sorted(keys): _lock(key)
    lookup = Q()
    if referencia: lookup |= Q(sistema_origen=sistema, referencia_externa=referencia)
    if idempotencia: lookup |= Q(sistema_origen=sistema, referencia_idempotencia=idempotencia)
    if keys:
        matches = list(Agenda.objects.filter(lookup).order_by('id'))
        if len(matches) > 1:
            raise ConflictoRegistro('La referencia y la clave de idempotencia corresponden a expedientes distintos.')
        if matches:
            existing = matches[0]
            if existing.referencia_externa != referencia or (existing.causante, existing.asunto, existing.tipo, existing.letra) != (causante, asunto, tipo, letra):
                raise ConflictoRegistro('La solicitud repetida tiene datos distintos al expediente original.')
            return existing, False
    # Los reintentos ya asignados siguen disponibles aun si se bloquean nuevas altas.
    if not ControlNumeracion.objects.filter(pk=1, habilitado=True).exists():
        raise NumeracionNoHabilitada()
    now = timezone.now()
    anio = timezone.localtime(now).year
    _lock(f'correlativo-anual:{anio}')
    counter, _ = CorrelativoAnual.objects.get_or_create(anio=anio, defaults={'ultimo_numero': 0})
    counter = CorrelativoAnual.objects.select_for_update().get(pk=counter.pk)
    # El contador historico se inicializa en migracion/confirmacion, nunca desde MAX sin lock.
    numero = counter.ultimo_numero + 1
    registro = Agenda.objects.create(numero=numero, anio=anio, fecha_hora=now,
        causante=causante, asunto=asunto, tipo=tipo, letra=letra,
        origen=f'SISTEMA_{sistema}' if sistema else Agenda.ORIGEN_MANUAL,
        sistema_origen=sistema, referencia_externa=referencia, referencia_idempotencia=idempotencia,
        creado_por=usuario, created_at=now, updated_at=now)
    counter.ultimo_numero = numero
    counter.save(update_fields=['ultimo_numero'])
    AuditoriaExpediente.objects.create(registro=registro, usuario=usuario, sistema=sistema,
        accion='CREAR_REGISTRO', datos={'numero': numero, 'anio': anio, 'origen': registro.origen, 'referencia': referencia})
    return registro, True


def cargar_manual(letra='', usuario=None, causante='', asunto='', tipo='', idempotencia=None):
    return crear_registro(causante=causante, asunto=asunto, tipo=tipo, letra=letra, usuario=usuario, idempotencia=idempotencia)


def reservar_automatico(letra='', referencia_externa=None, *, sistema, causante, asunto, tipo='', idempotencia=None):
    return crear_registro(causante=causante, asunto=asunto, tipo=tipo, letra=letra,
        sistema=sistema, referencia=referencia_externa, idempotencia=idempotencia)


@transaction.atomic
def registrar_sigedoc(registro_id, usuario):
    registro = Agenda.objects.select_for_update().get(pk=registro_id)
    if registro.anulado:
        raise ConflictoRegistro('Un expediente anulado no puede marcarse como registrado en SIGEDoc.')
    if registro.estado_sigedoc == Agenda.REGISTRADO:
        return registro
    now = timezone.now()
    registro.estado_sigedoc = Agenda.REGISTRADO
    registro.fecha_registro_sigedoc = now
    registro.registrado_sigedoc_por = usuario
    registro.updated_at = now
    registro.save(update_fields=['estado_sigedoc', 'fecha_registro_sigedoc', 'registrado_sigedoc_por', 'updated_at'])
    AuditoriaExpediente.objects.create(registro=registro, usuario=usuario, accion='REGISTRAR_SIGEDOC', datos={'numero_formateado': registro.numero_formateado})
    return registro


@transaction.atomic
def anular_registro(registro_id, usuario, motivo):
    if not motivo.strip(): raise ValidationError({'motivo': 'El motivo es obligatorio.'})
    registro = Agenda.objects.select_for_update().get(pk=registro_id)
    if registro.anulado: raise ConflictoRegistro('El expediente ya esta anulado.')
    now = timezone.now()
    registro.anulado = True
    registro.anulado_por = usuario
    registro.fecha_anulacion = now
    registro.motivo_anulacion = motivo.strip()
    registro.updated_at = now
    registro.save(update_fields=['anulado', 'anulado_por', 'fecha_anulacion', 'motivo_anulacion', 'updated_at'])
    AuditoriaExpediente.objects.create(registro=registro, usuario=usuario, accion='ANULAR_REGISTRO', motivo=motivo.strip(), datos={'numero_formateado': registro.numero_formateado})
    return registro
