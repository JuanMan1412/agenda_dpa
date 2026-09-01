from rest_framework import serializers

from .models import Agenda


class AgendaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agenda
        fields = [
            "id",
            "numero",
            "anio",
            "letra",
            "asunto",
            "causante",
            "origen",
            "referencia_externa",
            "fecha_hora",
            "estado",
            "fecha_carga_externa",
        ]
        read_only_fields = fields
