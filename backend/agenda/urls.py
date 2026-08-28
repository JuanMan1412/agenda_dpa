from django.urls import path

from .views import AgendaCargaManualView, AgendaListView, AgendaReservaExternaView

urlpatterns = [
    path("agenda/", AgendaListView.as_view(), name="agenda-listar"),
    path("agenda/manual/", AgendaCargaManualView.as_view(), name="agenda-manual"),
    path(
        "agenda/reservar/",
        AgendaReservaExternaView.as_view(),
        name="agenda-reservar-externo",
    ),
]
