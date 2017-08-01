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
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('sí', 'sí'),
            ('no', 'no'),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        value = self.value()
        if value:
            isnull = value == 'no'
            queryset = queryset.filter(geom__isnull=isnull)
        return queryset


class LugarVotacionAdmin(LeafletGeoAdmin):
    list_display = ('nombre', 'direccion', 'ciudad', 'circuito')
    list_display_links = ('nombre',)
    list_filter = (HasLatLongListFilter, 'circuito', 'circuito__seccion')


admin.site.register(LugarVotacion, LugarVotacionAdmin)

for model in (Seccion, Circuito, Mesa, Partido, Opcion, Eleccion, VotoMesaReportado):
    admin.site.register(model)


# Register your models here.
