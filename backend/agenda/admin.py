from django.contrib import admin
from .models import Agenda, AuditoriaExpediente, CorrelativoAnual, ControlNumeracion


class ConsultaAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None): return [field.name for field in self.model._meta.fields]
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


@admin.register(Agenda)
class AgendaAdmin(ConsultaAdmin):
    list_display = ('numero_formateado', 'fecha_hora', 'origen', 'causante', 'estado_sigedoc', 'anulado')
    list_filter = ('anio', 'origen', 'estado_sigedoc', 'anulado')
    search_fields = ('=numero', 'causante', 'asunto', 'letra', 'referencia_externa')
    ordering = ('-anio', '-numero')
    date_hierarchy = 'fecha_hora'


@admin.register(AuditoriaExpediente)
class AuditoriaAdmin(ConsultaAdmin):
    list_display = ('registro', 'accion', 'fecha_hora', 'usuario', 'sistema')
    list_filter = ('accion', 'sistema')


admin.site.register(CorrelativoAnual, ConsultaAdmin)
admin.site.register(ControlNumeracion, ConsultaAdmin)
