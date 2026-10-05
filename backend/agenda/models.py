from django.conf import settings
from django.db import models
from django.utils import timezone


def anio_actual():
    return timezone.localdate().year


class Agenda(models.Model):
    """Registro de expedientes sobre la tabla historica de Agenda."""
    ORIGEN_MANUAL = 'MESA_ENTRADA'
    ORIGEN_AUTOMATICO = 'SISTEMA_LEGADO'
    PENDIENTE = 'PENDIENTE'
    REGISTRADO = 'REGISTRADO'
    id = models.AutoField(primary_key=True)
    numero = models.PositiveIntegerField(editable=False)
    anio = models.PositiveSmallIntegerField(default=anio_actual, editable=False)
    letra = models.CharField(max_length=10, blank=True, default='')
    fecha_hora = models.DateTimeField(default=timezone.now, editable=False)
    causante = models.CharField(max_length=255, blank=True, default='')
    asunto = models.TextField(blank=True, default='')
    tipo = models.CharField(max_length=100, blank=True, default='')
    origen = models.CharField(max_length=100, editable=False)
    sistema_origen = models.CharField(max_length=80, blank=True, default='', editable=False)
    referencia_externa = models.CharField(max_length=255, null=True, blank=True, editable=False)
    referencia_idempotencia = models.CharField(max_length=255, null=True, blank=True, editable=False)
    estado_sigedoc = models.CharField(max_length=12, choices=[(PENDIENTE, 'Pendiente'), (REGISTRADO, 'Registrado')], default=PENDIENTE, editable=False)
    fecha_registro_sigedoc = models.DateTimeField(null=True, blank=True, editable=False)
    registrado_sigedoc_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='expedientes_sigedoc', editable=False)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='expedientes_creados', editable=False)
    anulado = models.BooleanField(default=False, editable=False)
    fecha_anulacion = models.DateTimeField(null=True, blank=True, editable=False)
    anulado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='expedientes_anulados', editable=False)
    motivo_anulacion = models.TextField(blank=True, default='', editable=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = 'agenda'
        ordering = ['-anio', '-numero']
        verbose_name = 'Registro de expediente'
        verbose_name_plural = 'Registros de expedientes'
        constraints = [
            models.UniqueConstraint(fields=['numero', 'anio'], name='expediente_numero_anio_unico'),
            models.UniqueConstraint(fields=['sistema_origen', 'referencia_externa'], condition=~models.Q(sistema_origen='') & models.Q(referencia_externa__isnull=False), name='expediente_referencia_unica'),
            models.UniqueConstraint(fields=['sistema_origen', 'referencia_idempotencia'], condition=models.Q(referencia_idempotencia__isnull=False), name='expediente_idempotencia_unica'),
            models.CheckConstraint(condition=models.Q(numero__gt=0), name='expediente_numero_positivo'),
        ]
        indexes = [models.Index(fields=['anio', 'estado_sigedoc', 'anulado'], name='expediente_estado_idx')]

    @property
    def numero_formateado(self):
        return f'{self.numero}/{self.anio}'

    def __str__(self):
        return self.numero_formateado


# Nombre conceptual, conservando el modelo y las rutas historicas de Django.
RegistroExpediente = Agenda


class CorrelativoAnual(models.Model):
    anio = models.PositiveSmallIntegerField(primary_key=True)
    ultimo_numero = models.PositiveIntegerField(default=0)


class ControlNumeracion(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    habilitado = models.BooleanField(default=False)
    anio_validado = models.PositiveSmallIntegerField(null=True)
    ultimo_numero_libro = models.PositiveIntegerField(null=True)
    confirmado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    fecha_confirmacion = models.DateTimeField(null=True)


class AuditoriaExpediente(models.Model):
    registro = models.ForeignKey(Agenda, null=True, on_delete=models.PROTECT, related_name='auditoria')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    sistema = models.CharField(max_length=80, blank=True, default='')
    fecha_hora = models.DateTimeField(default=timezone.now, editable=False)
    accion = models.CharField(max_length=40)
    datos = models.JSONField(default=dict)
    motivo = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['fecha_hora', 'id']
