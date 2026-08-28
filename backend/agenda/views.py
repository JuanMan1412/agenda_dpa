from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import EsAplicacionExterna, ExternoApiKeyAuthentication
from .models import Agenda
from .serializers import AgendaSerializer
from .services import cargar_manual, reservar_automatico


class AgendaListView(generics.ListAPIView):
    """Listado general (para la tabla del frontend)."""

    queryset = Agenda.objects.all()
    serializer_class = AgendaSerializer
    permission_classes = [permissions.AllowAny]


class AgendaCargaManualView(APIView):
    """
    Usada por el personal de mesa de entradas desde el frontend
    React. Requiere usuario logueado (ajustar el permission_class
    si usan otro esquema de auth, ej. JWT/session).
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        letra = request.data.get("letra")
        if not letra:
            return Response(
                {"detail": "El campo 'letra' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        registro = cargar_manual(letra=letra, usuario=request.user)
        return Response(registro, status=status.HTTP_201_CREATED)


class AgendaReservaExternaView(APIView):
    """
    Endpoint que consume la aplicación externa para pedir un
    número nuevo. Autenticación por API Key, no por usuario/login.
    """

    authentication_classes = [ExternoApiKeyAuthentication]
    permission_classes = [EsAplicacionExterna]

    def post(self, request):
        letra = request.data.get("letra")
        referencia_externa = request.data.get("referencia_externa")

        if not letra:
            return Response(
                {"detail": "El campo 'letra' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        registro = reservar_automatico(
            letra=letra, referencia_externa=referencia_externa
        )
        return Response(registro, status=status.HTTP_201_CREATED)
