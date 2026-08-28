from django.db import connection


def _crear_registro(letra, origen, referencia_externa=None):
    """
    Inserta un registro SIN especificar 'numero': la columna lo toma
    solo de agenda_numero_seq (ver db/schema.sql). Usamos SQL crudo
    a propósito acá, en vez del ORM, para no correr riesgo de que
    Django mande NULL o algún valor propio en esa columna.

    RETURNING nos da el número ya asignado en la misma consulta,
    sin necesidad de un segundo SELECT.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO agenda (letra, origen, referencia_externa)
            VALUES (%s, %s, %s)
            RETURNING id, numero, letra, origen, referencia_externa, fecha_hora;
            """,
            [letra, origen, referencia_externa],
        )
        columnas = [col[0] for col in cursor.description]
        fila = cursor.fetchone()
        return dict(zip(columnas, fila))


def cargar_manual(letra, usuario=None):
    return _crear_registro(letra=letra, origen="manual")


def reservar_automatico(letra, referencia_externa=None):
    return _crear_registro(
        letra=letra, origen="automatico", referencia_externa=referencia_externa
    )
