from django.urls import path

from .views import (
    AgendaCargaManualView,
    AgendaEstadisticasView,
    AgendaListView,
    AgendaMarcarCargadoView,
    AgendaReservaExternaView,
)

urlpatterns = [
    path("agenda/", AgendaListView.as_view(), name="agenda-listar"),
    path("agenda/estadisticas/", AgendaEstadisticasView.as_view(), name="agenda-estadisticas"),
    path("agenda/manual/", AgendaCargaManualView.as_view(), name="agenda-manual"),
    path("agenda/reservar/", AgendaReservaExternaView.as_view(), name="agenda-reservar-externo"),
    path("agenda/<int:pk>/cargar/", AgendaMarcarCargadoView.as_view(), name="agenda-marcar-cargado"),
]
