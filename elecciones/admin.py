
from django.db.models import Q
from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin
from .models import Seccion, Circuito, LugarVotacion, Mesa, Partido, Opcion, Eleccion, VotoMesaReportado


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
    lookup = 'asignacion_fiscales__isnull'

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
    lookup = 'asignacion_fiscal__isnull'



class LugarVotacionAdmin(LeafletGeoAdmin):

    def sección(o):
        return o.circuito.seccion.numero

    list_display = ('nombre', 'direccion', 'ciudad', 'circuito', sección, 'mesas_desde_hasta')
    list_display_links = ('nombre',)
    list_filter = (HasLatLongListFilter, TieneFiscalGeneral, 'circuito__seccion', 'circuito')
    search_fields = (
        'nombre', 'direccion', 'ciudad', 'barrio', 'mesas__numero'
    )


class MesaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'lugar_votacion')
    list_filter = (TieneFiscal, 'lugar_votacion__circuito__seccion', 'lugar_votacion__circuito')
    search_fields = (
        'numero', 'lugar_votacion__nombre', 'lugar_votacion__direccion',
        'lugar_votacion__ciudad', 'lugar_votacion__barrio',
    )



admin.site.register(LugarVotacion, LugarVotacionAdmin)
admin.site.register(Mesa, MesaAdmin)


for model in (Seccion, Circuito, Partido, Opcion, Eleccion, VotoMesaReportado):
    admin.site.register(model)


# Register your models here.
