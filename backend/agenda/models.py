from django.db import models


class Agenda(models.Model):
    """
    Este modelo apunta a la tabla 'agenda' que ya crearon con
    db/schema.sql en pgAdmin. managed = False: Django NO va a
    intentar crear/alterar esta tabla con sus migraciones, solo
    la lee y escribe.
    """

    ORIGEN_MANUAL = "manual"
    ORIGEN_AUTOMATICO = "automatico"
    ORIGEN_CHOICES = [
        (ORIGEN_MANUAL, "Manual"),
        (ORIGEN_AUTOMATICO, "Automático"),
    ]

    id = models.AutoField(primary_key=True)
    numero = models.IntegerField(unique=True)
    letra = models.CharField(max_length=10)
    origen = models.CharField(max_length=12, choices=ORIGEN_CHOICES)
    referencia_externa = models.CharField(max_length=100, null=True, blank=True)
    fecha_hora = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "agenda"
        ordering = ["-numero"]

    def __str__(self):
        return f"{self.numero} - {self.letra}"
