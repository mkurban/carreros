from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from djgeojson.views import GeoJSONLayerView
from .models import LugarVotacion


class LugaresVotacionGeoJSON(GeoJSONLayerView):
    model = LugarVotacion
    properties = ('id',) # 'popup_html',)

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(latitud__isnull=False)


class EscuelaDetailView(DetailView):
    template_name = "elecciones/detalle_escuela.html"
    model = LugarVotacion


# Create your views here.
class Mapa(TemplateView):
    template_name = "elecciones/mapa.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)


# Create your views here.
class Mapa1(TemplateView):
    template_name = "elecciones/mapa1.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)
