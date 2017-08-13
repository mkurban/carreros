from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.urls import reverse
from django.shortcuts import render, redirect
from djgeojson.views import GeoJSONLayerView
from .models import LugarVotacion, Circuito
from .forms import ReferentesForm
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test


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
            circuito.referentes.add(*form.cleaned_data['referentes'])
            return redirect('admin:elecciones_circuito_changelist')

    return render(request, 'elecciones/add_referentes.html', {'form':form, 'ids': ids, 'qs': qs})