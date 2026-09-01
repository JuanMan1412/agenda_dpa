from django.db import connection, transaction
from django.utils import timezone

from .models import Agenda


def _crear_registro(letra, origen, referencia_externa=None, asunto=None, causante=None, anio=None):
    """Assign a safe consecutive number within the selected year."""
    anio = anio or timezone.localdate().year

    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [anio])
        cursor.execute("SELECT COALESCE(MAX(numero), 0) + 1 FROM agenda WHERE anio = %s", [anio])
        numero = cursor.fetchone()[0]
        cursor.execute(
            """
            INSERT INTO agenda (numero, anio, letra, asunto, causante, origen, referencia_externa, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, numero, anio, letra, asunto, causante, origen,
                      referencia_externa, fecha_hora, estado, fecha_carga_externa;
            """,
            [numero, anio, letra, asunto, causante, origen, referencia_externa, Agenda.Estado.PENDIENTE],
        )
        columnas = [col[0] for col in cursor.description]
        return dict(zip(columnas, cursor.fetchone()))


def cargar_manual(letra, asunto, causante, usuario=None, anio=None):
    return _crear_registro(letra, Agenda.ORIGEN_MANUAL, asunto=asunto, causante=causante, anio=anio)


def reservar_automatico(letra, referencia_externa=None, asunto=None, causante=None, anio=None):
    return _crear_registro(letra, Agenda.ORIGEN_AUTOMATICO, referencia_externa, asunto, causante, anio)


def marcar_como_cargado(registro_id, referencia_externa=None):
    with transaction.atomic():
        registro = Agenda.objects.select_for_update().filter(pk=registro_id).first()
        if registro is None:
            return None

        campos_actualizados = []
        if referencia_externa is not None:
            registro.referencia_externa = referencia_externa
            campos_actualizados.append("referencia_externa")
        if registro.estado != Agenda.Estado.CARGADO:
            registro.estado = Agenda.Estado.CARGADO
            registro.fecha_carga_externa = timezone.now()
            campos_actualizados.extend(["estado", "fecha_carga_externa"])
        if campos_actualizados:
            registro.save(update_fields=campos_actualizados)
        return registro
