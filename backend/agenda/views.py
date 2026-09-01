from datetime import timedelta

from django.db.models import Avg, DurationField, ExpressionWrapper, F, Q
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import EsAplicacionExterna, ExternoApiKeyAuthentication
from .models import Agenda
from .serializers import AgendaSerializer
from .services import cargar_manual, marcar_como_cargado, reservar_automatico


def es_solo_letras(valor, permitir_espacios=False):
    return all(caracter.isalpha() or (permitir_espacios and caracter.isspace()) for caracter in valor)


class AgendaListView(generics.ListAPIView):
    serializer_class = AgendaSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Agenda.objects.all()
        estado = self.request.query_params.get("estado")
        buscar = self.request.query_params.get("buscar", "").strip()
        if estado in Agenda.Estado.values:
            queryset = queryset.filter(estado=estado)
        if buscar:
            filtros = Q(letra__icontains=buscar) | Q(asunto__icontains=buscar)
            filtros |= Q(causante__icontains=buscar) | Q(referencia_externa__icontains=buscar)
            if buscar.isdigit():
                filtros |= Q(numero=int(buscar)) | Q(anio=int(buscar))
            numero, separador, anio = buscar.partition("/")
            if separador and numero.isdigit() and anio.isdigit():
                filtros |= Q(numero=int(numero), anio=int(anio))
            queryset = queryset.filter(filtros)
        return queryset


class AgendaEstadisticasView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        inicio_hoy = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
        inicio_maniana = inicio_hoy + timedelta(days=1)
        cargados_hoy = Agenda.objects.filter(
            estado=Agenda.Estado.CARGADO,
            fecha_carga_externa__gte=inicio_hoy,
            fecha_carga_externa__lt=inicio_maniana,
        )
        promedio = cargados_hoy.aggregate(
            promedio=Avg(ExpressionWrapper(F("fecha_carga_externa") - F("fecha_hora"), output_field=DurationField()))
        )["promedio"]
        return Response({
            "pendientes": Agenda.objects.filter(estado=Agenda.Estado.PENDIENTE).count(),
            "cargados_hoy": cargados_hoy.count(),
            "tiempo_promedio_segundos": int(promedio.total_seconds()) if promedio else None,
        })


@method_decorator(csrf_exempt, name="dispatch")
class AgendaCargaManualView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        letra = request.data.get("letra")
        asunto = request.data.get("asunto")
        causante = request.data.get("causante")
        if not isinstance(letra, str) or not letra.strip():
            return Response({"detail": "El campo 'letra' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)
        if asunto is not None and not isinstance(asunto, str):
            return Response({"detail": "El asunto debe ser texto."}, status=status.HTTP_400_BAD_REQUEST)
        if causante is not None and not isinstance(causante, str):
            return Response({"detail": "El causante debe ser texto."}, status=status.HTTP_400_BAD_REQUEST)
        if not es_solo_letras(letra) or (causante and not es_solo_letras(causante, permitir_espacios=True)):
            return Response(
                {"detail": "La letra solo admite letras y el causante solo letras y espacios."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        registro = cargar_manual(
            letra.strip(),
            asunto.strip() if asunto else None,
            causante.strip() if causante else None,
        )
        return Response(registro, status=status.HTTP_201_CREATED)


class AgendaReservaExternaView(APIView):
    authentication_classes = [ExternoApiKeyAuthentication]
    permission_classes = [EsAplicacionExterna]

    def post(self, request):
        letra = request.data.get("letra")
        if not letra:
            return Response({"detail": "El campo 'letra' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)
        registro = reservar_automatico(
            letra=letra,
            referencia_externa=request.data.get("referencia_externa"),
            asunto=request.data.get("asunto"),
            causante=request.data.get("causante"),
        )
        return Response(registro, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name="dispatch")
class AgendaMarcarCargadoView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request, pk):
        referencia_externa = request.data.get("referencia_externa")
        if referencia_externa is not None and not isinstance(referencia_externa, str):
            return Response({"detail": "La referencia externa debe ser texto."}, status=status.HTTP_400_BAD_REQUEST)
        registro = marcar_como_cargado(pk, referencia_externa.strip() if referencia_externa is not None else None)
        if registro is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(AgendaSerializer(registro).data)
