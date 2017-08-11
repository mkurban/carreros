from django.contrib import admin
from django.urls import reverse
from leaflet.admin import LeafletGeoAdmin
from .models import Seccion, Circuito, LugarVotacion, Mesa, Partido, Opcion, Eleccion, VotoMesaReportado
from django.http import HttpResponseRedirect
from django_admin_row_actions import AdminRowActionsMixin


class HasLatLongListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'Tiene coordenadas'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'coordenadas'

    def lookups(self, request, model_admin):
        return (
            ('sí', 'sí'),
            ('no', 'no'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            isnull = value == 'no'
            queryset = queryset.filter(geom__isnull=isnull)
        return queryset


class TieneFiscal(admin.SimpleListFilter):
    title = 'Tiene fiscal'
    parameter_name = 'fiscal'
    lookup = 'asignacion__isnull'

    def lookups(self, request, model_admin):
        return (
            ('sí', 'sí'),
            ('no', 'no'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            isnull = value == 'no'
            queryset = queryset.filter(**{self.lookup: isnull})
        return queryset


class TieneFiscalGeneral(TieneFiscal):
    title = 'Tiene fiscal general'
    lookup = 'asignacion__isnull'


def mostrar_en_mapa(modeladmin, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    ids = ",".join(selected)
    mapa_url = reverse('mapa')
    return HttpResponseRedirect(f'{mapa_url}?ids={ids}')

mostrar_en_mapa.short_description = "Mostrar seleccionadas en el mapa"


class LugarVotacionAdmin(AdminRowActionsMixin, LeafletGeoAdmin):

    def sección(o):
        return o.circuito.seccion.numero

    list_display = ('nombre', 'direccion', 'ciudad', 'circuito', sección, 'mesas_desde_hasta', 'electores')
    list_display_links = ('nombre',)
    list_filter = (HasLatLongListFilter, TieneFiscalGeneral, 'circuito__seccion', 'circuito')
    search_fields = (
        'nombre', 'direccion', 'ciudad', 'barrio', 'mesas__numero'
    )
    show_full_result_count = False
    actions = [mostrar_en_mapa]

    def get_row_actions(self, obj):
        row_actions = [
            {
                'label': 'Mesas',
                'url': reverse('admin:elecciones_mesa_changelist') + f'?lugar_votacion__id={obj.id}',
                'enabled': True,
            }
        ]
        if obj.asignacion_actual:
            url = reverse('admin:fiscales_asignacionfiscalgeneral_change', args=(obj.asignacion_actual.id,))
            label_asignacion = 'Editar asignación'

        else:
            url = reverse('admin:fiscales_asignacionfiscalgeneral_add') + f'?lugar_votacion={obj.id}'
            label_asignacion = 'Asignar fiscal general'

        row_actions.append({
            'label': f'{label_asignacion}',
            'url': url,
            'enabled': True
        })
        row_actions += super().get_row_actions(obj)
        return row_actions


class MesaAdmin(AdminRowActionsMixin, admin.ModelAdmin):
    list_display = ('numero', 'lugar_votacion')
    list_filter = (TieneFiscal, 'lugar_votacion__circuito__seccion', 'lugar_votacion__circuito')
    search_fields = (
        'numero', 'lugar_votacion__nombre', 'lugar_votacion__direccion',
        'lugar_votacion__ciudad', 'lugar_votacion__barrio',
    )

    def get_row_actions(self, obj):
        row_actions = [
            {
                'label': 'Escuela',
                'url': reverse('admin:elecciones_lugarvotacion_changelist') + f'?id={obj.lugar_votacion.id}',
                'enabled': True,
            }
        ]
        if obj.asignacion_actual:
            url = reverse('admin:fiscales_asignacionfiscaldemesa_change', args=(obj.asignacion_actual.id,))
            label_asignacion = 'Editar asignación'

        else:
            url = reverse('admin:fiscales_asignacionfiscaldemesa_add') + f'?mesa={obj.id}'
            label_asignacion = 'Asignar fiscal'

        row_actions.append({
            'label': f'{label_asignacion}',
            'url': url,
            'enabled': True
        })

        row_actions += super().get_row_actions(obj)
        return row_actions



class PartidoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'nombre')
    list_display_links = list_display


class CircuitoAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'seccion')
    list_display_links = list_display
    list_filter = ('seccion',)
    search_fields = (
        'nombre', 'numero',
    )



admin.site.register(Circuito, CircuitoAdmin)
admin.site.register(Partido, PartidoAdmin)
admin.site.register(LugarVotacion, LugarVotacionAdmin)
admin.site.register(Mesa, MesaAdmin)


for model in (Seccion, Opcion, Eleccion, VotoMesaReportado):
    admin.site.register(model)


# Register your models here.
