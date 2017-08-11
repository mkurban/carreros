import json

from django.http import HttpResponse
from django.template import loader
from .models import *
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.urls import reverse
from djgeojson.views import GeoJSONLayerView
from .models import LugarVotacion
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator


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
        return qs.filter(latitud__isnull=False)


class EscuelaDetailView(StaffOnlyMixing, DetailView):
    template_name = "elecciones/detalle_escuela.html"
    model = LugarVotacion


# Create your views here.
class Mapa(StaffOnlyMixing, TemplateView):
    template_name = "elecciones/mapa.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        geojson_url = reverse("geojson")
        if 'ids' in self.request.GET:
            query = self.request.GET.urlencode()
            geojson_url += f'?{query}'
        context['geojson_url'] = geojson_url
        return context

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
        return json.dumps([{'key': op.opcion.nombre, 'y': op.votos} for op in ops if not op.opcion.nombre.find("TOTAL")==0])
    mesa = Mesa.objects.get(numero=nro)
    reporte = VotoMesaReportado.objects.filter(mesa__numero=mesa.numero, votos__isnull=False)
    rep_chart = extrac_chart_data(reporte)
    parte = VotoMesaOficial.objects.filter(mesa__numero=mesa.numero, votos__isnull=False)
    par_chart = extrac_chart_data(parte)
    template = loader.get_template('elecciones/mesa.html')
    context = {
        'mesa': mesa,
        'reporte': reporte,
        'rep_chart': rep_chart,
        'parte_de_mesa':parte,
        'par_chart': par_chart
    }
    return HttpResponse(template.render(context, request))
