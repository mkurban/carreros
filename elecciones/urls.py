# -*- coding: utf-8 -*-
from django.conf.urls import url
from . import views


urlpatterns = [
    url('^escuelas.geojson$', views.LugaresVotacionGeoJSON.as_view(), name='geojson'),
    url('^escuelas/(?P<pk>\d+)$', views.EscuelaDetailView.as_view(), name='detalle_escuela'),
    url('^mapa/$', views.Mapa.as_view(), name='mapa'),

    url('^mapa/(?P<elecciones_slug>\w+)/$', views.MapaResultadosOficiales.as_view(), name='mapa-resultados'),
    url('^mapa/(?P<elecciones_slug>\w+)/(?P<pk>\d+)$', views.ResultadoEscuelaDetailView.as_view()),

    url('^mapa/(?P<elecciones_slug>\w+)/resultados.geojson$', views.ResultadosOficialesGeoJSON.as_view(), name='resultados-geojson'),

    url('^resultados$', views.resultados, name='resultados'),
    url('^resultados/mesa/(?P<nro>\d+)$', views.resultados_mesa, name='resultados_mesa'),
    url('^resultados/mesas_ids$', views.resultados_mesas_ids, name='resultados_mesas_ids'),
    url('^resultados/mesas$', views.resultados_mesas, name='resultados_mesas'),
    url(r'^fiscal_mesa/', views.fiscal_mesa, name='fiscal_mesa'),
]
