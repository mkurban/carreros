# -*- coding: utf-8 -*-
from django.conf.urls import url
from . import views
from fancy_cache import cache_page


cached = cache_page(600)


urlpatterns = [
    url('^escuelas.geojson$', cached(views.LugaresVotacionGeoJSON.as_view()), name='geojson'),
    url('^escuelas/(?P<pk>\d+)$', views.EscuelaDetailView.as_view(), name='detalle_escuela'),
    url('^mapa/$', cached(views.Mapa.as_view()), name='mapa'),

    # url('^mapa/(?P<elecciones_slug>\w+)/$', cached(views.MapaResultadosOficiales.as_view()), name='mapa-resultados'),

    url('^mapa/(?P<elecciones_slug>\w+)/(?P<pk>\d+)$', views.ResultadoEscuelaDetailView.as_view()),
    url('^mapa/(?P<elecciones_slug>\w+)/resultados.geojson$', cached(views.ResultadosOficialesGeoJSON.as_view()), name='resultados-geojson'),
    url('^resultados/mapa$', cached(views.MapaResultadosOficiales.as_view()), name='resultados-mapa'),

    url('^resultados/(?P<eleccion_id>\d+)/$', cached(views.ResultadosEleccion.as_view()), name='resultados-eleccion'),
    url('^resultados$', cached(views.Resultados.as_view()), name='resultados'),

    # url('^resultados$', views.resultados, name='resultados'),
    # url('^resultados/mesa/(?P<nro>\d+)$', views.resultados_mesa, name='resultados_mesa'),
    # url('^resultados/mesas_ids$', views.resultados_mesas_ids, name='resultados_mesas_ids'),
    # url('^resultados/mesas$', views.resultados_mesas, name='resultados_mesas'),
    url(r'^fiscal_mesa/', views.fiscal_mesa, name='fiscal_mesa'),
]
