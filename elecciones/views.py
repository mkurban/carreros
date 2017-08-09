from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.urls import reverse
from djgeojson.views import GeoJSONLayerView
from .models import LugarVotacion


class LugaresVotacionGeoJSON(GeoJSONLayerView):
    model = LugarVotacion
    properties = ('id', 'color')    # 'popup_html',)

    def get_queryset(self):
        qs = super().get_queryset()
        ids = self.request.GET.get('ids')
        if ids:
            qs = qs.filter(id__in=ids.split(','))
        return qs.filter(latitud__isnull=False)


class EscuelaDetailView(DetailView):
    template_name = "elecciones/detalle_escuela.html"
    model = LugarVotacion


# Create your views here.
class Mapa(TemplateView):
    template_name = "elecciones/mapa.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        geojson_url = reverse("geojson")
        if 'ids' in self.request.GET:
            query = self.request.GET.urlencode()
            geojson_url += f'?{query}'
        context['geojson_url'] = geojson_url
        return context
