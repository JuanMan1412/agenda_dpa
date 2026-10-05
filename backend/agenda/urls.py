from django.urls import path
from .views import (AgendaListView, AgendaCargaManualView, AgendaReservaExternaView,
    RegistroListView, RegistroDetailView, RegistrarSigedocView, AnularRegistroView,
    ResumenView, IntegracionDetailView, IntegracionReferenciaView)

urlpatterns = [
    path('agenda/', AgendaListView.as_view(), name='agenda-listar'),
    path('agenda/manual/', AgendaCargaManualView.as_view(), name='agenda-manual'),
    path('agenda/reservar/', AgendaReservaExternaView.as_view(), name='agenda-reservar-externo'),
    path('expedientes/', RegistroListView.as_view(), name='expediente-listar'),
    path('expedientes/manual/', AgendaCargaManualView.as_view(), name='expediente-manual'),
    path('expedientes/resumen/', ResumenView.as_view(), name='expediente-resumen'),
    path('expedientes/<int:pk>/', RegistroDetailView.as_view(), name='expediente-detalle'),
    path('expedientes/<int:pk>/registrar-sigedoc/', RegistrarSigedocView.as_view(), name='expediente-sigedoc'),
    path('expedientes/<int:pk>/anular/', AnularRegistroView.as_view(), name='expediente-anular'),
    path('integraciones/expedientes/reservar/', AgendaReservaExternaView.as_view(), name='integracion-reservar'),
    path('integraciones/expedientes/por-referencia/', IntegracionReferenciaView.as_view(), name='integracion-referencia'),
    path('integraciones/expedientes/<int:pk>/', IntegracionDetailView.as_view(), name='integracion-detalle'),
]
