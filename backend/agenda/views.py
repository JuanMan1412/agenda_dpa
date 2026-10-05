from django.db.models import Count, Max, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, serializers, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, ValidationError
from roles.permissions import AgendaPermission
from .authentication import EsAplicacionExterna, ExternoApiKeyAuthentication
from .models import Agenda
from .serializers import AgendaSerializer, DetalleSerializer, CrearSerializer, ReservaSerializer, AnularSerializer, ConfirmacionSerializer
from .services import cargar_manual, reservar_automatico, registrar_sigedoc, anular_registro, estado_numeracion


def registros():
    return Agenda.objects.select_related('creado_por', 'registrado_sigedoc_por', 'anulado_por')


class FiltrosSerializer(serializers.Serializer):
    anio = serializers.IntegerField(required=False, min_value=1, max_value=9999)
    q = serializers.CharField(required=False, max_length=200, allow_blank=True)
    estado = serializers.ChoiceField(choices=['TODOS', 'PENDIENTE', 'REGISTRADO', 'ANULADO'], required=False)
    origen = serializers.CharField(required=False, max_length=100, allow_blank=True)
    hoy = serializers.BooleanField(required=False)
    orden = serializers.ChoiceField(choices=['fecha_asc', 'numero_desc'], required=False)


def filtrar(queryset, params):
    serializer = FiltrosSerializer(data=params)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    if 'anio' in data: queryset = queryset.filter(anio=data['anio'])
    if data.get('origen'): queryset = queryset.filter(origen=data['origen'])
    estado = data.get('estado')
    if estado == 'ANULADO': queryset = queryset.filter(anulado=True)
    elif estado in {'PENDIENTE', 'REGISTRADO'}: queryset = queryset.filter(anulado=False, estado_sigedoc=estado)
    if data.get('hoy'): queryset = queryset.filter(fecha_hora__date=timezone.localdate())
    query = data.get('q', '').strip()
    if query:
        parts = query.split('/')
        if len(parts) == 2 and all(part.isdigit() for part in parts):
            queryset = queryset.filter(numero=int(parts[0]), anio=int(parts[1]))
        else:
            lookup = Q(causante__icontains=query) | Q(asunto__icontains=query) | Q(referencia_externa__icontains=query)
            if query.isdigit(): lookup |= Q(numero=int(query))
            queryset = queryset.filter(lookup)
    return queryset.order_by('fecha_hora', 'id') if data.get('orden') == 'fecha_asc' else queryset.order_by('-anio', '-numero')


def idempotency(request):
    value = request.headers.get('Idempotency-Key')
    if value is not None:
        value = value.strip()
        if not value or len(value) > 255: raise ValidationError({'idempotencia': 'La clave debe tener entre 1 y 255 caracteres.'})
    return value


class RegistroPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class AgendaListView(generics.ListAPIView):
    serializer_class = AgendaSerializer
    permission_classes = [permissions.IsAuthenticated, AgendaPermission]
    def get_queryset(self): return filtrar(registros(), self.request.query_params)


class RegistroListView(AgendaListView):
    pagination_class = RegistroPagination


class AgendaCargaManualView(APIView):
    permission_classes = [permissions.IsAuthenticated, AgendaPermission]
    operacion = 'crear_registro'
    def post(self, request):
        serializer = CrearSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        registro, created = cargar_manual(usuario=request.user, idempotencia=idempotency(request), **serializer.validated_data)
        return Response(AgendaSerializer(registro).data, status=201 if created else 200)


class RegistroDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated, AgendaPermission]
    serializer_class = DetalleSerializer
    queryset = registros().prefetch_related('auditoria__usuario')


class RegistrarSigedocView(APIView):
    permission_classes = [permissions.IsAuthenticated, AgendaPermission]
    operacion = 'registrar_sigedoc'
    def post(self, request, pk):
        serializer = ConfirmacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        get_object_or_404(Agenda, pk=pk)
        registro = registrar_sigedoc(pk, request.user)
        return Response(DetalleSerializer(registro).data)


class AnularRegistroView(APIView):
    permission_classes = [permissions.IsAuthenticated, AgendaPermission]
    operacion = 'anular_registro'
    def post(self, request, pk):
        serializer = AnularSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        get_object_or_404(Agenda, pk=pk)
        registro = anular_registro(pk, request.user, serializer.validated_data['motivo'])
        return Response(DetalleSerializer(registro).data)


class ResumenView(APIView):
    permission_classes = [permissions.IsAuthenticated, AgendaPermission]
    def get(self, request):
        queryset = registros()
        if request.query_params.get('anio'):
            s = FiltrosSerializer(data={'anio': request.query_params['anio']})
            s.is_valid(raise_exception=True)
            queryset = queryset.filter(anio=s.validated_data['anio'])
        counts = queryset.aggregate(ultimo_numero=Max('numero'),
            pendientes=Count('id', filter=Q(anulado=False, estado_sigedoc=Agenda.PENDIENTE)),
            registrados_hoy=Count('id', filter=Q(anulado=False, fecha_registro_sigedoc__date=timezone.localdate())),
            anulados=Count('id', filter=Q(anulado=True)))
        latest = queryset.order_by('-anio', '-numero').first()
        counts['ultimo_numero'] = latest.numero if latest else None
        return Response({**counts, 'ultimo_numero_formateado': latest.numero_formateado if latest else None,
            'anios': list(Agenda.objects.order_by('-anio').values_list('anio', flat=True).distinct()),
            'origenes': list(Agenda.objects.order_by('origen').values_list('origen', flat=True).distinct()),
            'numeracion': estado_numeracion()})


class AgendaReservaExternaView(APIView):
    authentication_classes = [ExternoApiKeyAuthentication]
    permission_classes = [EsAplicacionExterna]
    permiso_servicio = 'reservar'
    def post(self, request):
        data = request.data.copy()
        if 'referencia_externa' in data:
            if 'referencia' in data and data['referencia'] != data['referencia_externa']:
                raise ValidationError({'referencia': 'Las referencias no coinciden.'})
            data['referencia'] = data.pop('referencia_externa')
        serializer = ReservaSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = dict(serializer.validated_data)
        supplied_system = values.pop('sistema', request.auth.sistema).strip().upper()
        if supplied_system != request.auth.sistema:
            raise PermissionDenied('La credencial no pertenece al sistema solicitado.')
        reference = values.pop('referencia')
        registro, created = reservar_automatico(sistema=request.auth.sistema, referencia_externa=reference,
            idempotencia=idempotency(request), **values)
        return Response(AgendaSerializer(registro).data, status=201 if created else 200)


class IntegracionDetailView(generics.RetrieveAPIView):
    authentication_classes = [ExternoApiKeyAuthentication]
    permission_classes = [EsAplicacionExterna]
    permiso_servicio = 'consultar'
    serializer_class = AgendaSerializer
    def get_queryset(self): return registros().filter(sistema_origen=self.request.auth.sistema)


class IntegracionReferenciaView(APIView):
    authentication_classes = [ExternoApiKeyAuthentication]
    permission_classes = [EsAplicacionExterna]
    permiso_servicio = 'consultar'
    def get(self, request):
        reference = request.query_params.get('referencia', '').strip()
        if not reference: raise ValidationError({'referencia': 'La referencia es obligatoria.'})
        registro = get_object_or_404(registros(), sistema_origen=request.auth.sistema, referencia_externa=reference)
        return Response(AgendaSerializer(registro).data)
