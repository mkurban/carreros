import json
from urllib import parse

from django.http import HttpResponse
from django.http import Http404
from django.template import loader
from .models import *
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.urls import reverse
from django.shortcuts import render, redirect
from django.contrib import messages
from djgeojson.views import GeoJSONLayerView
from .models import LugarVotacion, Circuito
from fiscales.models import  Fiscal
from .forms import ReferentesForm, LoggueConMesaForm
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
    if len(mesas) > 0:
        reporte = VotoMesaReportado.objects.filter(mesa__numero__in=idss, opcion__obligatorio=True, votos__isnull=False)\
            .values('opcion__nombre','opcion__nombre_corto','opcion__partido__nombre_corto') \
            .annotate(votos=Sum("votos")) \
            .order_by("-votos")
        rep_otros = VotoMesaReportado.objects.filter(mesa__numero__in=idss, opcion__obligatorio=False, votos__isnull=False) \
            .aggregate(Sum("votos"))
        reporte_l = [o for o in reporte]
        reporte_l = reporte_l + ([{'opcion__nombre':"Otros", "votos": rep_otros["votos__sum"]}] if rep_otros["votos__sum"] else [])
        reporte_l = (reporte_l[1:] + [reporte_l[0]] if reporte_l else reporte_l)

        parte = VotoMesaOficial.objects.filter(mesa__numero__in=idss, opcion__obligatorio=True, votos__isnull=False) \
            .values('opcion__nombre','opcion__nombre_corto','opcion__partido__nombre_corto') \
            .annotate(votos=Sum("votos")) \
            . order_by("-votos")
        par_otros = VotoMesaOficial.objects.filter(mesa__numero__in=idss, opcion__obligatorio=False, votos__isnull=False) \
            .aggregate(Sum("votos"))
        parte_l = [o for o in parte]
        parte_l = parte_l + ([{'opcion__nombre':"Otros", "votos": par_otros["votos__sum"]}] if par_otros["votos__sum"] else [])
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
            'par_chart': par_chart
        }
        return HttpResponse(template.render(context, request))
    else:
        raise Http404("Error, Mesas no encontradas")


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