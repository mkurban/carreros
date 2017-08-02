from django.db.models import Q
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import Fiscal, AsignacionFiscalGeneral, AsignacionFiscalDeMesa, Organizacion
from .forms import FiscalForm
from prensa.models import DatoDeContacto
from prensa.forms import DatoDeContactoModelForm


class ContactoAdminInline(GenericTabularInline):
    model = DatoDeContacto
    form = DatoDeContactoModelForm


class AsignadoFilter(admin.SimpleListFilter):
    title = 'Asignación'
    parameter_name = 'asignado'

    def lookups(self, request, model_admin):
        return (
            ('sí', 'sí'),
            ('no', 'no'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            isnull = value == 'no'
            general = Q(tipo='general') & Q(asignacion_escuela__isnull=isnull)
            de_mesa = Q(tipo='de_mesa') & Q(asignacion_mesa__isnull=isnull)
            queryset = queryset.filter(general | de_mesa)
        return queryset


class FiscalAdmin(admin.ModelAdmin):
    form = FiscalForm
    list_display = ('__str__', 'direccion', 'organizacion', 'dni', 'telefonos')
    search_fields = (
        'apellido', 'direccion', 'dni',
        'asignacion_escuela__lugar_votacion__nombre',
        'asignacion_mesa__mesa__lugar_votacion__nombre'
    )
    list_display_links = ('__str__',)
    list_filter = (AsignadoFilter, 'tipo', 'organizacion')
    readonly_fields = ('mesas_desde_hasta',)
    inlines = [
        ContactoAdminInline,
    ]


class AsignacionFiscalGeneralAdmin(admin.ModelAdmin):
    list_display = ('fiscal', 'lugar_votacion', 'ingreso', 'egreso')
    list_filter = ('ingreso', 'egreso')
    search_fields = (
        'fiscal__apellido', 'fiscal__direccion', 'fiscal__dni',
        'lugar_votacion__nombre',
        'lugar_votacion__direccion',
        'lugar_votacion__barrio',
        'lugar_votacion__ciudad',
    )
    raw_id_fields = ("lugar_votacion", "fiscal")


class AsignacionFiscalDeMesaAdmin(admin.ModelAdmin):
    list_display = ('fiscal', 'mesa', 'ingreso', 'egreso')
    raw_id_fields = ("mesa", "fiscal")
    list_filter = ('ingreso', 'egreso')
    search_fields = (
        'fiscal__apellido', 'fiscal__direccion', 'fiscal__dni',
        'lugar_votacion__nombre',
        'lugar_votacion__direccion',
        'lugar_votacion__barrio',
        'lugar_votacion__ciudad',
    )


admin.site.register(AsignacionFiscalGeneral, AsignacionFiscalGeneralAdmin)
admin.site.register(AsignacionFiscalDeMesa, AsignacionFiscalDeMesaAdmin)
admin.site.register(Fiscal, FiscalAdmin)
admin.site.register(Organizacion)
