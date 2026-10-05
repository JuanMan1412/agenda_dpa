from rest_framework import serializers
from .models import Agenda, AuditoriaExpediente


def nombre_usuario(user):
    if not user: return None
    return user.nombre_completo or ' '.join(filter(None, [user.nombre, user.apellido])) or user.username


class AuditoriaSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()
    def get_usuario_nombre(self, obj): return nombre_usuario(obj.usuario)
    class Meta:
        model = AuditoriaExpediente
        fields = ['id', 'fecha_hora', 'accion', 'usuario', 'usuario_nombre', 'sistema', 'datos', 'motivo']


class AgendaSerializer(serializers.ModelSerializer):
    numero_formateado = serializers.ReadOnlyField()
    fecha_registro = serializers.DateTimeField(source='fecha_hora', read_only=True)
    creado_por_nombre = serializers.SerializerMethodField()
    registrado_sigedoc_por_nombre = serializers.SerializerMethodField()
    anulado_por_nombre = serializers.SerializerMethodField()
    def get_creado_por_nombre(self, obj): return nombre_usuario(obj.creado_por)
    def get_registrado_sigedoc_por_nombre(self, obj): return nombre_usuario(obj.registrado_sigedoc_por)
    def get_anulado_por_nombre(self, obj): return nombre_usuario(obj.anulado_por)
    class Meta:
        model = Agenda
        fields = ['id', 'numero', 'anio', 'numero_formateado', 'letra', 'fecha_hora', 'fecha_registro',
            'causante', 'asunto', 'tipo', 'origen', 'sistema_origen', 'referencia_externa', 'referencia_idempotencia',
            'estado_sigedoc', 'fecha_registro_sigedoc', 'registrado_sigedoc_por', 'registrado_sigedoc_por_nombre',
            'creado_por', 'creado_por_nombre', 'anulado', 'fecha_anulacion', 'anulado_por', 'anulado_por_nombre',
            'motivo_anulacion', 'created_at', 'updated_at']
        read_only_fields = fields


class DetalleSerializer(AgendaSerializer):
    auditoria = AuditoriaSerializer(many=True, read_only=True)
    class Meta(AgendaSerializer.Meta):
        fields = AgendaSerializer.Meta.fields + ['auditoria']


class CrearSerializer(serializers.Serializer):
    causante = serializers.CharField(max_length=255)
    asunto = serializers.CharField(max_length=5000)
    tipo = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    letra = serializers.CharField(max_length=10, required=False, allow_blank=True, default='')
    def validate(self, attrs):
        forbidden = set(self.initial_data) - set(self.fields)
        if forbidden: raise serializers.ValidationError({key: 'Este campo no puede enviarse.' for key in sorted(forbidden)})
        return attrs


class ReservaSerializer(CrearSerializer):
    referencia = serializers.CharField(max_length=255)
    sistema = serializers.CharField(max_length=80, required=False)


class AnularSerializer(serializers.Serializer):
    motivo = serializers.CharField(max_length=2000)


class ConfirmacionSerializer(serializers.Serializer):
    confirmar = serializers.BooleanField()
    def validate_confirmar(self, value):
        if not value: raise serializers.ValidationError('Debes confirmar la registracion en SIGEDoc.')
        return value
