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
            general = Q(
                tipo='general',
                asignacion_escuela__isnull=isnull,
                asignacion_escuela__eleccion__slug='generales2017'
            )
            de_mesa = Q(
                tipo='de_mesa',
                asignacion_mesa__isnull=isnull,
                asignacion_mesa__mesa__eleccion__slug='generales2017'
            )
            queryset = queryset.filter(general | de_mesa)
        return queryset


class ReferenteFilter(admin.SimpleListFilter):
    title = 'Referente'
    parameter_name = 'referente'

    def lookups(self, request, model_admin):
        return (
            ('sí', 'sí'),
            ('no', 'no'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            isnull = value == 'no'
            queryset = queryset.filter(es_referente_de_circuito__isnull=isnull).distinct()
        return queryset



class FiscalAdmin(AdminRowActionsMixin, admin.ModelAdmin):

    def get_row_actions(self, obj):
        row_actions = []
        if obj.user:
            row_actions.append(
                {
                    'label': f'Loguearse como {obj.nombres}',
                    'url': f'/hijack/{obj.user.id}/',
                    'enabled': True,
                }
            )

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

        escuelas_ids = ','.join(str(id) for id in obj.escuelas.values_list('id', flat=True))
        row_actions.append({
                'label': 'Escuelas asignadas',
                'url': reverse('admin:elecciones_lugarvotacion_changelist') + f'?id__in={escuelas_ids}',
                'enabled': True
        })

        row_actions += super().get_row_actions(obj)
        return row_actions

    def telefonos(o):
        return ' / '.join(o.telefonos)

    def asignado_a(o):
        if o.asignacion:
            return o.asignacion.lugar_votacion if o.es_general else o.asignacion.mesa


    form = FiscalForm
    list_display = ('__str__', 'tipo', 'direccion', 'organizacion', 'dni', telefonos, asignado_a)
    search_fields = (
        'apellido', 'nombres', 'direccion', 'dni',
        'asignacion_escuela__lugar_votacion__nombre',
        'asignacion_mesa__mesa__lugar_votacion__nombre'
    )
    list_display_links = ('__str__',)
    list_filter = ('estado', 'email_confirmado', AsignadoFilter, 'tipo', ReferenteFilter, 'organizacion')
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
        row_actions = []
        if obj.fiscal:
            row_actions.append(
                {
                    'label': 'Ver fiscal',
                    'url': reverse('admin:fiscales_fiscal_changelist') + f'?id={obj.fiscal.id}',
                    'enabled': True,
                }
            )
        row_actions += super().get_row_actions(obj)
        return row_actions


class AsignacionFiscalGeneralAdmin(AsignacionFiscalAdmin):

    list_filter = ('eleccion', 'lugar_votacion__circuito',) + AsignacionFiscalAdmin.list_filter

    list_display = ('fiscal', 'lugar_votacion', 'ingreso', 'egreso', 'comida')
    search_fields = (
        'fiscal__apellido', 'fiscal__nombres', 'fiscal__direccion', 'fiscal__dni',
        'lugar_votacion__nombre',
        'lugar_votacion__direccion',
        'lugar_votacion__barrio',
        'lugar_votacion__ciudad',
    )
    raw_id_fields = ("lugar_votacion", "fiscal")


class AsignacionFiscalDeMesaAdmin(AsignacionFiscalAdmin):

    list_filter = ('mesa__eleccion', 'mesa__lugar_votacion__circuito',) + AsignacionFiscalAdmin.list_filter

    list_display = ('fiscal', 'mesa', 'ingreso', 'egreso', 'comida')
    raw_id_fields = ("mesa", "fiscal")
    search_fields = (
        'fiscal__apellido', 'fiscal__nombres', 'fiscal__direccion', 'fiscal__dni',
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
