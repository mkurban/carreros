from django.db.models import Q
from django.urls import reverse
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import Fiscal, AsignacionFiscalGeneral, AsignacionFiscalDeMesa, Organizacion
from .forms import FiscalForm
from prensa.models import DatoDeContacto
from prensa.forms import DatoDeContactoModelForm
from django_admin_row_actions import AdminRowActionsMixin
from django.contrib.admin.filters import DateFieldListFilter


class FechaIsNull(DateFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        super().__init__(field, request, params, model, model_admin, field_path)
        self.links = self.links[-2:]


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


class FiscalAdmin(AdminRowActionsMixin, admin.ModelAdmin):

    def get_row_actions(self, obj):

        row_actions = [
            {
                'label': f'Loguearse como {obj.nombres}',
                'url': f'/hijack/{obj.user.id}/',
                'enabled': True,
            }
        ]
        label_asignacion = 'Editar asignación a' if  obj.asignacion else 'Asignar a'
        if obj.es_general and obj.asignacion:
            url = reverse('admin:fiscales_asignacionfiscalgeneral_change', args=(obj.asignacion.id,))
        elif obj.es_general and not obj.asignacion:
            url = reverse('admin:fiscales_asignacionfiscalgeneral_add') + f'?fiscal={obj.id}'
        elif obj.asignacion:
            url = reverse('admin:fiscales_asignacionfiscaldemesa_change', args=(obj.asignacion.id,))
        else:
            url = reverse('admin:fiscales_asignacionfiscaldemesa_add') + f'?fiscal={obj.id}'

        row_actions.append({
            'label': f'{label_asignacion} escuela' if obj.es_general else f'{label_asignacion} mesa',
            'url': url,
            'enabled': True
        })

        row_actions += super().get_row_actions(obj)
        return row_actions

    def telefonos(o):
        return ' / '.join(o.telefonos)

    form = FiscalForm
    list_display = ('__str__', 'tipo', 'direccion', 'organizacion', 'dni', telefonos)
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


def asignar_comida(modeladmin, request, queryset):
    queryset.update(comida='asignada')


class AsignacionFiscalAdmin(AdminRowActionsMixin, admin.ModelAdmin):
    list_filter = (('ingreso', FechaIsNull), ('egreso', FechaIsNull), 'comida')
    actions = [asignar_comida]

    def get_row_actions(self, obj):
        row_actions = [
            {
                'label': 'Ver fiscal',
                'url': reverse('admin:fiscales_fiscal_changelist') + f'?q={obj.fiscal.dni}',
                'enabled': True,
            }
        ]
        row_actions += super().get_row_actions(obj)
        return row_actions


class AsignacionFiscalGeneralAdmin(AsignacionFiscalAdmin):
    list_display = ('fiscal', 'lugar_votacion', 'ingreso', 'egreso', 'comida')
    search_fields = (
        'fiscal__apellido', 'fiscal__direccion', 'fiscal__dni',
        'lugar_votacion__nombre',
        'lugar_votacion__direccion',
        'lugar_votacion__barrio',
        'lugar_votacion__ciudad',
    )
    raw_id_fields = ("lugar_votacion", "fiscal")


class AsignacionFiscalDeMesaAdmin(AsignacionFiscalAdmin):
    list_display = ('fiscal', 'mesa', 'ingreso', 'egreso', 'comida')
    raw_id_fields = ("mesa", "fiscal")
    search_fields = (
        'fiscal__apellido', 'fiscal__direccion', 'fiscal__dni',
        'mesa__numero',
        'mesa__lugar_votacion__nombre',
        'mesa__lugar_votacion__direccion',
        'mesa__lugar_votacion__barrio',
        'mesa__lugar_votacion__ciudad',
    )



admin.site.register(AsignacionFiscalGeneral, AsignacionFiscalGeneralAdmin)
admin.site.register(AsignacionFiscalDeMesa, AsignacionFiscalDeMesaAdmin)
admin.site.register(Fiscal, FiscalAdmin)
admin.site.register(Organizacion)
