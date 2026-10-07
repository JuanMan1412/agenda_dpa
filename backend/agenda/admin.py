from django.contrib import admin
from django import forms
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from .models import Agenda, AuditoriaExpediente, CorrelativoAnual, ControlNumeracion
from .services import confirmar_numeracion, estado_numeracion, puede_confirmar_numeracion


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

class ConfirmarNumeracionForm(forms.Form):
    anio = forms.IntegerField(label='Año verificado', widget=forms.HiddenInput)
    ultimo_numero_libro = forms.IntegerField(label='Último número usado en el libro físico', min_value=0,
        max_value=2147483646, help_text='Para comenzar en 15235, ingresá 15234. Si el libro aún no tiene números, ingresá 0.')
    confirmar = forms.BooleanField(label='Confirmo que comparé este número con el libro físico de Mesa de Entrada')


@admin.register(ControlNumeracion)
class ControlNumeracionAdmin(ConsultaAdmin):
    def has_module_permission(self, request):
        return puede_confirmar_numeracion(request.user)

    def has_view_permission(self, request, obj=None):
        return puede_confirmar_numeracion(request.user)

    def changelist_view(self, request, extra_context=None):
        if not self.has_view_permission(request):
            raise PermissionDenied
        state = estado_numeracion()
        form = ConfirmarNumeracionForm(request.POST if request.method == 'POST' else None,
            initial={'anio': state['anio'], 'ultimo_numero_libro': state['ultimo_numero_consumido']})
        if request.method == 'POST' and form.is_valid():
            try:
                next_number = confirmar_numeracion(anio=form.cleaned_data['anio'],
                    ultimo_numero_libro=form.cleaned_data['ultimo_numero_libro'], usuario=request.user)
            except ValueError as exc:
                form.add_error(None, str(exc))
            else:
                self.message_user(request, f'Asignaciones habilitadas. Próximo expediente: {next_number}/{state["anio"]}.')
                return redirect(reverse('admin:agenda_controlnumeracion_changelist'))
        context = {**self.admin_site.each_context(request), 'opts': self.model._meta,
            'title': 'Configurar numeración de expedientes', 'form': form, 'numeracion': state,
            'control': ControlNumeracion.objects.filter(pk=1).first()}
        return TemplateResponse(request, 'admin/agenda/confirmar_numeracion.html', context)
