from django.db import models


class Agenda(models.Model):
    """
    Registro correlativo de ingresos. PostgreSQL asigna numero y
    fecha_hora mediante los valores por defecto de la tabla.
    """

    ORIGEN_MANUAL = "manual"
    ORIGEN_AUTOMATICO = "automatico"
    ORIGEN_CHOICES = [
        (ORIGEN_MANUAL, "Manual"),
        (ORIGEN_AUTOMATICO, "Automático"),
    ]

    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente de carga externa"
        CARGADO = "cargado", "Cargado en sistema externo"

    id = models.AutoField(primary_key=True)
    numero = models.IntegerField()
    anio = models.PositiveSmallIntegerField()
    letra = models.CharField(max_length=10)
    asunto = models.TextField(null=True, blank=True)
    causante = models.CharField(max_length=200, null=True, blank=True)
    origen = models.CharField(max_length=12, choices=ORIGEN_CHOICES)
    referencia_externa = models.CharField(max_length=100, null=True, blank=True)
    fecha_hora = models.DateTimeField()
    estado = models.CharField(
        max_length=10,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    fecha_carga_externa = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "agenda"
        ordering = ["-anio", "-numero"]
        constraints = [
            models.UniqueConstraint(
                fields=["numero", "anio"],
                name="agenda_numero_anio_unico",
            ),
        ]

    def __str__(self):
        return f"{self.numero}/{self.anio} - {self.letra}"
