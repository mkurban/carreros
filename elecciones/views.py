from functools import lru_cache

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q, F, Sum
from django.shortcuts import render, redirect
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

#    def options(self, request, *args, **kwargs):
#        response = super().options(request, *args, **kwargs)
#        print("Holas...")
#        print(response)
#        response.content_type='text/plain'
#        print(response)
#        return response


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



# Create your views here.
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


class ResultadosOficiales(StaffOnlyMixing, TemplateView):
    template_name = "elecciones/resultados_es.html"

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
        sum_por_partido, otras_opciones = ResultadosOficiales.agregaciones_por_partido()
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
            result_piechart = [{'key': k, 'y': v[0]} for k, v in result.items()]
            resultados[eleccion] = {'tabla': result,
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

        results = self.get_resultados()
        context['resultados'] = results
        return context


class TextTemplateView(TemplateView):
    def render_to_response(self, context, **response_kwargs):
        response_kwargs['content_type'] = 'text/plain'
        return super(TemplateView, self).render_to_response(context, **response_kwargs)

class ResultadosOficialesEleccion(StaffOnlyMixing, TextTemplateView):
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
        if 'seccion' in self.request.GET:
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
            if 'seccion' in self.request.GET:
                lookups = Q(circuito__seccion__in=self.filtros)

            elif 'circuito' in self.request.GET:
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
        sum_por_partido, otras_opciones = ResultadosOficiales.agregaciones_por_partido()

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
        result_piechart = [{'key': k, 'y': v[0]} for k, v in result.items()]
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

        context['eleccion_id'] = self.kwargs["eleccion_id"]
        context['resultados'] = self.get_resultados(self.kwargs["eleccion_id"])
        return context


class ResultadosOficialesElecciones(StaffOnlyMixing, TemplateView):
    template_name = "elecciones/resultados_elecciones.html"

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
        sum_por_partido, otras_opciones = ResultadosOficiales.agregaciones_por_partido()
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
            result_piechart = [{'key': k.nombre_corto if isinstance(k, Partido) else str(k), 'y': v[0]} for k, v in result.items()]
            resultados[eleccion] = {'tabla': result,
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
        context['resultados'] = self.get_resultados()
        return context

"""

def resultados(request):
    mesas_list = Mesa.objects.filter(votomesaoficial__eleccion__isnull=False)
    mesas_list2 = Mesa.objects.filter(votomesareportado__eleccion__isnull=False)
    mesas_list = set(set(mesas_list) | set(mesas_list2))
    template = loader.get_template('elecciones/resultados.html')
    context = {
        'mesas_list': mesas_list,
    }
    return HttpResponse(template.render(context, request))

def resultados_mesa(request, nro):
    def extrac_chart_data(ops):
        return json.dumps([{'key': op.opcion.nombre_corto, 'y': op.votos} for op in ops if not op.opcion.nombre.find("TOTAL")==0])
    mesa = Mesa.objects.get(numero=nro)
    reporte = VotoMesaReportado.objects.filter(mesa__numero=mesa.numero, votos__isnull=False)
    rep_chart = extrac_chart_data(reporte)
    parte = VotoMesaOficial.objects.filter(mesa__numero=mesa.numero, votos__isnull=False)
    par_chart = extrac_chart_data(parte)
    template = loader.get_template('elecciones/resultados_mesa.html')
    context = {
        'mesa': mesa,
        'reporte': reporte,
        'rep_chart': rep_chart,
        'parte_de_mesa':parte,
        'par_chart': par_chart
    }
    return HttpResponse(template.render(context, request))

def resultados_mesas_ids(request):
    idss = []
    if 'ids' in request.GET:
        query = request.GET.urlencode()
        ids = f'?{query}'
        ids = parse.unquote(ids)
        idss = ids[5:].split(",")
        mesas = Mesa.objects.filter(id__in=idss)
    else:
        mesas = Mesa.objects.filter(es_testigo=True)

    if len(mesas) > 0:
        nums = [str(m.numero) for m in mesas]
        return redirect('/elecciones/resultados/mesas?ids=' + ",".join(nums))
    else:
        raise Http404("Error, Mesas no encontradas")


def resultados_mesas(request):
    idss = []

    if 'ids' in request.GET:
        query = request.GET.urlencode()
        ids = f'?{query}'
        ids = parse.unquote(ids)
        idss = ids[5:].split(",")
        mesas = Mesa.objects.filter(numero__in=idss)
    else:
        mesas = Mesa.objects.filter(es_testigo=True)

    if len(mesas) > 0:
        reporte = VotoMesaReportado.objects.filter(mesa__numero__in=idss, opcion__obligatorio=True, votos__isnull=False)\
            .values('opcion__nombre','opcion__nombre_corto','opcion__partido__nombre_corto') \
            .annotate(votos=Sum("votos")) \
            .order_by("-votos")
        rep_otros = VotoMesaReportado.objects.filter(mesa__numero__in=idss, opcion__obligatorio=False, votos__isnull=False) \
            .aggregate(Sum("votos"))
        reporte_l = [o for o in reporte]
        reporte_l = reporte_l + ([{'opcion__nombre':"Otros", "votos": rep_otros["votos__sum"]}] if rep_otros["votos__sum"] else [])
        if len(reporte_l) > 0:
            total_votos= float(reporte_l[0]["votos"])
            for e in reporte_l:
                if total_votos > 0:
                    e["porcentaje"] = "{:10.2f}".format(100.0 * (float(e["votos"]) / total_votos))
                else:
                    e["porcentaje"] = 0.0
        reporte_l = (reporte_l[1:] + [reporte_l[0]] if reporte_l else reporte_l)

        parte = VotoMesaOficial.objects.filter(mesa__numero__in=idss, opcion__obligatorio=True, votos__isnull=False) \
            .values('opcion__nombre','opcion__nombre_corto','opcion__partido__nombre_corto') \
            .annotate(votos=Sum("votos")) \
            . order_by("-votos")
        par_otros = VotoMesaOficial.objects.filter(mesa__numero__in=idss, opcion__obligatorio=False, votos__isnull=False) \
            .aggregate(Sum("votos"))
        parte_l = [o for o in parte]
        parte_l = parte_l + ([{'opcion__nombre':"Otros", "votos": par_otros["votos__sum"]}] if par_otros["votos__sum"] else [])
        if len(parte_l) > 0:
            total_votos_p= float(parte_l[0]["votos"])
            for e in parte_l:
                if total_votos_p > 0:
                    e["porcentaje"] = "{:10.2f}".format(100.0 * (float(e["votos"]) / total_votos))
                else:
                    e["porcentaje"] = 0.0
        parte_l = (parte_l[1:] + [parte_l[0]] if parte_l else parte_l)

        def extract_chart_data(ops, is_parte):
            return json.dumps([{'key': op["opcion__nombre_corto"], 'y': op["votos"]} \
                               for op in ops \
                               if not op["opcion__nombre"].find("TOTAL")==0] \
                              + ([{'key':"Otros", 'y':rep_otros["votos__sum"]}] if not is_parte else [{'key':"Otros", 'y':par_otros["votos__sum"]}]))
        rep_chart = extract_chart_data(reporte, False)
        par_chart = extract_chart_data(parte, True)

        template = loader.get_template('elecciones/resultados_mesas.html')
        context = {
            'ids': idss,
            'mesas': mesas,
            'reporte': reporte_l,
            'rep_chart': rep_chart,
            'parte_de_mesa':parte_l,
            'par_chart': par_chart,
        }
        return HttpResponse(template.render(context, request))
    else:
        raise Http404("Error, Mesas no encontradas")
"""

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



class Resultados(StaffOnlyMixing, TemplateView):
    template_name = "elecciones/resultados.html"


    @classmethod
    @lru_cache(128)
    def agregaciones(cls):

        opciones = {}

        for id in Opcion.objects.values_list('id', flat=True):
            opciones[str(id)] = Sum(Case(When(opcion__id=id, then=F('votos')),
                                         output_field=IntegerField()))

        return opciones

    @property
    @lru_cache(128)
    def filtros(self):
        """a partir de los argumentos de urls, devuelve
        listas de seccion / circuito etc. para filtrar """
        if 'mesa' in self.request.GET:
            return Mesa.objects.filter(id__in=self.request.GET.getlist('mesa'))
        elif 'lugarvotacion' in self.request.GET:
            return LugarVotacion.objects.filter(id__in=self.request.GET.getlist('lugarvotacion'))
        elif 'circuito' in self.request.GET:
            return Circuito.objects.filter(id__in=self.request.GET.getlist('circuito'))
        elif 'seccion' in self.request.GET:
            return Seccion.objects.filter(id__in=self.request.GET.getlist('seccion'))


    @property
    @lru_cache(128)
    def electores(self):
        lookups = Q()
        meta = {}
        for eleccion in Eleccion.objects.all():

            if self.filtros:

                if 'mesa' in self.request.GET:
                    lookups = Q(id__in=self.filtros)

                elif 'lugarvotacion' in self.request.GET:
                    lookups = Q(lugar_votacion__in=self.filtros)

                elif 'circuito' in self.request.GET:
                    lookups = Q(lugar_votacion__circuito__in=self.filtros)

                elif 'seccion' in self.request.GET:
                    lookups = Q(lugar_votacion__circuito__seccion__in=self.filtros)

            mesas = Mesa.objects.filter(eleccion=eleccion).filter(lookups).distinct()
            electores = mesas.aggregate(v=Sum('electores'))['v']
            meta[eleccion] = electores or 0
        return meta


    def get_resultados(self):
        lookups = Q()
        resultados = {}
        agregaciones = Resultados.agregaciones()
        for eleccion in Eleccion.objects.all():

            if self.filtros:

                if 'mesa' in self.request.GET:
                    lookups = Q(mesa__in=self.filtros)

                elif 'lugarvotacion' in self.request.GET:
                    lookups = Q(mesa__lugar_votacion__in=self.filtros)

                elif 'circuito' in self.request.GET:
                    lookups = Q(mesa__circuito__in=self.filtros)

                elif 'seccion' in self.request.GET:
                    lookups = Q(mesa__circuito__seccion__in=self.filtros)


            electores = self.electores[eleccion]
            # primero para partidos
            result = VotoMesaReportado.objects.filter(
                Q(mesa__eleccion=eleccion) & lookups
            ).aggregate(
                **agregaciones
            )
            result = {Opcion.objects.get(id=k): v for k, v in result.items() if v is not None}

            positivos = sum(v for k, v in result.items() if k.es_partido)

            total = sum(result.values())
            result = {k: (v, f'{v*100/total:.2f}') for k, v in result.items()}
            resultados[eleccion] = {'tabla': result,
                                    'electores': electores,
                                    'positivos': positivos,
                                    'escrutados': total,
                                    'participacion': f'{total*100/electores:.2f}' if electores else '-'
                                    }
        return resultados


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
            context['para'] = 'Buenos Aires'

        context['secciones'] = Seccion.objects.all()
        context['resultados'] = self.get_resultados()
        context['menu_activo'] = self.menu_activo()
        return context
