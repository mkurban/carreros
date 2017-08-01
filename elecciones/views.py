from django.views.generic.base import TemplateView
from djgeojson.views import GeoJSONLayerView
from .models import LugarVotacion


class LugaresVotacionGeoJSON(GeoJSONLayerView):
    model = LugarVotacion

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(latitud__isnull=False)


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
