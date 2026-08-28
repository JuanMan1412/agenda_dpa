from rest_framework import serializers

from .models import Agenda


class AgendaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agenda
        fields = [
            "id",
            "numero",
            "letra",
            "origen",
            "referencia_externa",
            "fecha_hora",
        ]
        read_only_fields = fields
