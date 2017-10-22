from functools import lru_cache
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q, F, Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.text import get_text_list
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from djgeojson.views import GeoJSONLayerView

from django.http import HttpResponse
from django.views import View

from fiscales.models import Fiscal
from .forms import ReferentesForm, LoggueConMesaForm
from .models import *
from .models import LugarVotacion, Circuito


class StaffOnlyMixing:

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class LugaresVotacionGeoJSON(GeoJSONLayerView):
    model = LugarVotacion
    properties = ('id', 'color')    # 'popup_html',)

    def get_queryset(self):
        qs = super().get_queryset()
        ids = self.request.GET.get('ids')
        if ids:
            qs = qs.filter(id__in=ids.split(','))
        elif 'todas' in self.request.GET:
            return qs
        elif 'testigo' in self.request.GET:
            qs = qs.filter(mesas__es_testigo=True).distinct()

        return qs


class ResultadosOficialesGeoJSON(GeoJSONLayerView):
    model = LugarVotacion
    properties = ('id', 'nombre', 'direccion_completa',
                  'seccion', 'circuito', 'resultados_oficiales')

    def get_queryset(self):
        qs = super().get_queryset()
        if 'seccion' in self.request.GET:
            return qs.filter(circuito__seccion__id__in=self.request.GET.getlist('seccion'))
        elif 'circuito' in self.request.GET:
            return qs.filter(circuito__id__in=self.request.GET.getlist('circuito'))
        elif 'lugarvotacion' in self.request.GET:
            return qs.filter(id__in=self.request.GET.getlist('lugarvotacion'))

        elif 'mesa' in self.request.GET:
            return qs.filter(mesas__id__in=self.request.GET.getlist('mesa')).distinct()

        return qs


class EscuelaDetailView(StaffOnlyMixing, DetailView):
    template_name = "elecciones/detalle_escuela.html"
    model = LugarVotacion


class ResultadoEscuelaDetailView(StaffOnlyMixing, DetailView):
    template_name = "elecciones/resultados_escuela.html"
    model = LugarVotacion


    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        sum_por_partido = {}
        for nombre, id in Partido.objects.values_list('nombre', 'id'):
            sum_por_partido[nombre] = Sum(Case(When(opcion__partido__id=id, then=F('votos')),
                             output_field=IntegerField()))

        for nombre, id in Opcion.objects.filter(id__in=[16, 17, 18, 19]).values_list('nombre', 'id'):
            sum_por_partido[nombre] = Sum(Case(When(opcion__id=id, then=F('votos')),
                             output_field=IntegerField()))


        result = VotoMesaOficial.objects.filter(mesa__eleccion__id=1, mesa__lugar_votacion=self.object).aggregate(
            **sum_por_partido
        )
        total = sum(v for v in result.values() if v)
        result = {k: (v, f'{v*100/total:.2f}') for k, v in result.items() if v}
        context['resultados'] = result
        return context


class Mapa(StaffOnlyMixing, TemplateView):
    template_name = "elecciones/mapa.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        geojson_url = reverse("geojson")
        if 'ids' in self.request.GET:
            query = self.request.GET.urlencode()
            geojson_url += f'?{query}'
        elif 'testigo' in self.request.GET:
            query = 'testigo=si'
            geojson_url += f'?{query}'

        context['geojson_url'] = geojson_url
        return context


class MapaResultadosOficiales(StaffOnlyMixing, TemplateView):
    template_name = "elecciones/mapa_resultados.html"


    @classmethod
    @lru_cache(128)
    def agregaciones_por_partido(cls):
        sum_por_partido = {}
        otras_opciones = {}
        for id in Partido.objects.values_list('id', flat=True):
            sum_por_partido[str(id)] = Sum(Case(When(opcion__partido__id=id, then=F('votos')),
                                                output_field=IntegerField()))

        for nombre, id in Opcion.objects.filter(id__in=[16, 17, 18, 19]).values_list('nombre', 'id'):
            otras_opciones[nombre] = Sum(Case(When(opcion__id=id, then=F('votos')),
                                              output_field=IntegerField()))

        return sum_por_partido, otras_opciones

    @property
    @lru_cache(128)
    def filtros(self):
        """a partir de los argumentos de urls, devuelve
        listas de seccion / circuito etc. para filtrar """
        if 'seccion' in self.request.GET:
            return Seccion.objects.filter(id__in=self.request.GET.getlist('seccion'))
        elif 'circuito' in self.request.GET:
            return Circuito.objects.filter(id__in=self.request.GET.getlist('circuito'))
        elif 'lugarvotacion' in self.request.GET:
            return LugarVotacion.objects.filter(id__in=self.request.GET.getlist('lugarvotacion'))
        elif 'mesa' in self.request.GET:
            return Mesa.objects.filter(id__in=self.request.GET.getlist('mesa'))

    @property
    @lru_cache(128)
    def electores(self):
        lookups = Q()
        meta = {}
        for eleccion in Eleccion.objects.all():

            if self.filtros:
                if 'seccion' in self.request.GET:
                    lookups = Q(circuito__seccion__in=self.filtros)

                elif 'circuito' in self.request.GET:
                    lookups = Q(circuito__in=self.filtros)

                elif 'lugarvotacion' in self.request.GET:
                    lookups = Q(id__in=self.filtros)

                elif 'mesa' in self.request.GET:
                        lookups = Q(mesas__id__in=self.filtros, mesas__eleccion=eleccion)

            escuelas = LugarVotacion.objects.filter(lookups).distinct()
            electores = escuelas.aggregate(v=Sum('electores'))['v']
            if electores and 'mesa' in self.request.GET:
                # promediamos los electores por mesa
                electores = electores * self.filtros.count() // Mesa.objects.filter(lugar_votacion__in=escuelas, eleccion=eleccion).count()
            meta[eleccion] = electores or 0
        return meta


    def get_resultados(self):
        lookups = Q()
        resultados = {}
        sum_por_partido, otras_opciones = MapaResultadosOficiales.agregaciones_por_partido()
        for eleccion in Eleccion.objects.all():

            if self.filtros:
                if 'seccion' in self.request.GET:
                    lookups = Q(mesa__lugar_votacion__circuito__seccion__in=self.filtros)

                elif 'circuito' in self.request.GET:
                    lookups = Q(mesa__lugar_votacion__circuito__in=self.filtros)

                elif 'lugarvotacion' in self.request.GET:
                    lookups = Q(mesa__lugar_votacion__in=self.filtros)

                elif 'mesa' in self.request.GET:
                    lookups = Q(mesa__id__in=self.filtros)

            electores = self.electores[eleccion]
            # primero para partidos
            result = VotoMesaReportado.objects.filter(
                Q(mesa__eleccion=eleccion) & lookups
            ).aggregate(
                **sum_por_partido
            )
            result = {Partido.objects.get(id=k): v for k, v in result.items() if v is not None}

            positivos = sum(result.values())

            # no positivos
            result_opc = VotoMesaReportado.objects.filter(
                Q(mesa__eleccion=eleccion) & lookups
            ).aggregate(
                **otras_opciones
            )
            result_opc = {k: v for k, v in result_opc.items() if v is not None}
            result.update(result_opc)

            total = sum(result.values())
            result = {k: (v, f'{v*100/total:.2f}') for k, v in result.items()}

            result = {k: (v, f'{v*100/total:.2f}') for k, v in result.items()}
            result_piechart = [{'key': k, 'y': v[0]} for k, v in result.items()]

            resultados[eleccion] = {'tabla': result,
                                    'electores': electores,
                                    'positivos': positivos,
                                    'escrutados': total,
                                    'participacion': f'{total*100/electores:.2f}'} if electores else '-'
        return resultados


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['geojson_url'] = reverse("resultados-geojson", args=['paso2017']) + f'?{self.request.GET.urlencode()}'
        if self.filtros:
            context['para'] = get_text_list(list(self.filtros), " y ")
        else:
            context['para'] = 'Córdoba'

        context['resultados'] = self.get_resultados()
        return context


class ResultadosEleccion(StaffOnlyMixing, TemplateView):
    template_name = "elecciones/resultados_eleccion.html"

    @classmethod
    @lru_cache(128)
    def agregaciones_por_partido(cls):
        sum_por_partido = {}
        otras_opciones = {}
        for id in Partido.objects.values_list('id', flat=True):
            sum_por_partido[str(id)] = Sum(Case(When(opcion__partido__id=id, then=F('votos')),
                                                output_field=IntegerField()))

        for nombre, id in Opcion.objects.filter(id__in=[16, 17, 18, 19]).values_list('nombre', 'id'):
            otras_opciones[nombre] = Sum(Case(When(opcion__id=id, then=F('votos')),
                                              output_field=IntegerField()))

        return sum_por_partido, otras_opciones

    @property
    @lru_cache(128)
    def filtros(self):
        """a partir de los argumentos de urls, devuelve
        listas de seccion / circuito etc. para filtrar """
        if self.kwargs.get('tipo') == 'seccion':
            return Seccion.objects.filter(numero=self.kwargs.get('numero'))
        if self.kwargs.get('tipo') == 'circuito':
            return Circuito.objects.filter(numero=self.kwargs.get('numero'))

        elif 'seccion' in self.request.GET:
            return Seccion.objects.filter(id__in=self.request.GET.getlist('seccion'))


        elif 'circuito' in self.request.GET:
            return Circuito.objects.filter(id__in=self.request.GET.getlist('circuito'))
        elif 'lugarvotacion' in self.request.GET:
            return LugarVotacion.objects.filter(id__in=self.request.GET.getlist('lugarvotacion'))
        elif 'mesa' in self.request.GET:
            return Mesa.objects.filter(id__in=self.request.GET.getlist('mesa'))

    @lru_cache(128)
    def electores(self, eleccion_id):

        lookups = Q()
        meta = {}
        if self.filtros:
            if self.filtros.model is Seccion:
                lookups = Q(circuito__seccion__in=self.filtros)

            elif self.filtros.models is Circuito:
                lookups = Q(circuito__in=self.filtros)

            elif 'lugarvotacion' in self.request.GET:
                lookups = Q(id__in=self.filtros)

            elif 'mesa' in self.request.GET:
                lookups = Q(mesas__id__in=self.filtros, mesas__eleccion_id=eleccion_id)

        escuelas = LugarVotacion.objects.filter(lookups).distinct()
        electores = escuelas.aggregate(v=Sum('electores'))['v']
        if electores and 'mesa' in self.request.GET:
            # promediamos los electores por mesa
            electores = electores * self.filtros.count() // Mesa.objects.filter(lugar_votacion__in=escuelas, eleccion_id=eleccion_id).count()
        return electores or 0


    def get_resultados(self, eleccion_id):
        lookups = Q()
        resultados = {}
        sum_por_partido, otras_opciones = ResultadosEleccion.agregaciones_por_partido()

        if self.filtros:
            if 'seccion' in self.request.GET:
                lookups = Q(mesa__lugar_votacion__circuito__seccion__in=self.filtros)

            elif 'circuito' in self.request.GET:
                lookups = Q(mesa__lugar_votacion__circuito__in=self.filtros)

            elif 'lugarvotacion' in self.request.GET:
                lookups = Q(mesa__lugar_votacion__in=self.filtros)

            elif 'mesa' in self.request.GET:
                lookups = Q(mesa__id__in=self.filtros)

        electores = self.electores(eleccion_id)
        # primero para partidos
        result = VotoMesaReportado.objects.filter(
            Q(mesa__eleccion_id=eleccion_id) & lookups
        ).aggregate(
            **sum_por_partido
        )
        result = {Partido.objects.get(id=k): v for k, v in result.items() if v is not None}

        positivos = sum(result.values())

        # no positivos
        result_opc = VotoMesaReportado.objects.filter(
            Q(mesa__eleccion_id=eleccion_id) & lookups
        ).aggregate(
            **otras_opciones
        )
        result_opc = {k: v for k, v in result_opc.items() if v is not None}
        result.update(result_opc)

        total = sum(result.values())
        result = {k: (v, f'{v*100/total:.2f}') for k, v in result.items()}
        result_piechart = [
            {'key': str(k),
             'y': v[0],
             'color': k.color  if not isinstance(k, str) else '#FFFFFF'} for k, v in result.items()
        ]
        resultados = {'tabla': result,
                      'result_piechart': result_piechart,
                      'electores': electores,
                      'positivos': positivos,
                      'escrutados': total,
                      'participacion': f'{total*100/electores:.2f}'} if electores else '-'
        return resultados

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.filtros:
            context['para'] = get_text_list(list(self.filtros), " y ")
        else:
            context['para'] = 'Córdoba'

        context['object'] = get_object_or_404(Eleccion, id=self.kwargs["eleccion_id"])
        context['eleccion_id'] = self.kwargs["eleccion_id"]
        context['resultados'] = self.get_resultados(self.kwargs["eleccion_id"])
        return context

    def render_to_response(self, context, **response_kwargs):
        d = {}
        chart = context['resultados']['result_piechart']

        d['chart_values'] = [v['y'] for v in chart]
        d['chart_keys'] = [v['key'] for v in chart]
        d['chart_colors'] = [v['color'] for v in chart]

        d['content'] = render_to_string(self.template_name, context, request=self.request)
        d['metadata'] = render_to_string(
            'elecciones/tabla_resultados_metadata.html',
            context,
            request=self.request
        )
        return JsonResponse(d)


class Resultados(StaffOnlyMixing, TemplateView):
    template_name = "elecciones/resultados.html"

    @property
    @lru_cache(128)
    def filtros(self):
        """a partir de los argumentos de urls, devuelve
        listas de seccion / circuito etc. para filtrar """
        if 'seccion' in self.request.GET:
            return Seccion.objects.filter(id__in=self.request.GET.getlist('seccion'))
        elif 'circuito' in self.request.GET:
            return Circuito.objects.filter(id__in=self.request.GET.getlist('circuito'))
        elif 'lugarvotacion' in self.request.GET:
            return LugarVotacion.objects.filter(id__in=self.request.GET.getlist('lugarvotacion'))
        elif 'mesa' in self.request.GET:
            return Mesa.objects.filter(id__in=self.request.GET.getlist('mesa'))

    def menu_activo(self):
        if not self.filtros:
            return []
        elif isinstance(self.filtros[0], Seccion):
            return (self.filtros[0], None)
        elif isinstance(self.filtros[0], Circuito):
            return (self.filtros[0].seccion, self.filtros[0])


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.filtros:
            context['para'] = get_text_list(list(self.filtros), " y ")
        else:
            context['para'] = 'Córdoba'
        context['elecciones'] = Eleccion.objects.all().order_by('-id')
        context['secciones'] = Seccion.objects.all()
        context['menu_activo'] = self.menu_activo()

        return context


class ResultadosProyectadosEleccion(StaffOnlyMixing, TemplateView):
    template_name = "elecciones/proyecciones.html"

    @property
    @lru_cache(128)
    def filtros(self):
        pass

    @property
    @lru_cache(128)
    def mesas(self):
        return Mesa.objects.filter(eleccion_id=3).order_by("numero")

    @property
    @lru_cache(128)
    def grupos(self):
        secciones_no_capital = list(Seccion.objects.all().exclude(id=1).order_by("numero"))
#        circuitos_capital= list(Circuito.objects.filter(seccion__id=1).order_by("numero"))
        return secciones_no_capital # + circuitos_capital

    def mesas_para_grupo(self, grupo):
        return [mesa for mesa in self.mesas if mesa.grupo_tabla_proyecciones == grupo]

    def resumen_mesa(self, mesa):
        resultados = mesa.votomesareportado_set.all()
        resumen = {}
        resumen["mesa"] = str(mesa)
        resumen["electores"] = mesa.electores

        def valor_resultado(nom_corto):
            res = 0
            try:
                res = resultados.get(opcion__nombre_corto=nom_corto)
            except:
                pass
            return res

        for nc in ["Total", "Cambiemos", "UPC", "FCC"]:
            resumen[nc] = valor_resultado(nc)

        votos_no_positivos = sum([valor_resultado(n) for n in ["NULOS", "RECURRIDOS", "IMPUGNADOS", "En Blanco"]])
        resumen["Positivos"] = resumen["Total"] - votos_no_positivos

        return resumen

    def resumen_grupo(self, grupo):
        resumen = [self.resumen_mesa(m) for m in self.mesas_para_grupo(grupo)]
        return resumen

    @property
    @lru_cache(128)
    def filas_tabla(self):
        return {("Seccion" if isinstance(g, Seccion) else "Circuito")+" No "+str(g.numero)
                : self.resumen_grupo(g)
                for g in self.grupos}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['para'] = 'Córdoba'
        context['eleccion'] = Eleccion.objects.filter(id=3)
        context['filas_tabla'] = self.filas_tabla

        return context


@user_passes_test(lambda u: u.is_superuser)
def asignar_referentes(request):
    ids = request.GET.get('ids')
    if not ids:
        return redirect('admin:elecciones_circuito_changelist')

    qs = Circuito.objects.filter(id__in=ids.split(','))
    initial = Circuito.objects.get(id=ids[0]).referentes.all()

    form = ReferentesForm(request.POST if request.method == 'POST' else None,
                          initial={'referentes': initial})
    if form.is_valid():
        for circuito in qs:
            circuito.referentes.set(form.cleaned_data['referentes'])
        return redirect('admin:elecciones_circuito_changelist')

    return render(request, 'elecciones/add_referentes.html', {'form':form, 'ids': ids, 'qs': qs})


@user_passes_test(lambda u: u.is_superuser)
def fiscal_mesa(request):
    form = LoggueConMesaForm(request.POST if request.method == 'POST' else None)

    if form.is_valid():
        f = Fiscal.objects.filter(asignacion_escuela__lugar_votacion__mesas__numero=form.cleaned_data['mesa']).first()
        if f:
            return redirect(f'/hijack/{f.user.id}/',)
        else:
            messages.warning(request, "mesa no existe o no sin fiscal")

    return render(request, 'elecciones/add_referentes.html', {'form':form})

