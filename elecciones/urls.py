# -*- coding: utf-8 -*-
from django.conf.urls import url
from . import views


urlpatterns = [
    url('^escuelas.geojson$', views.LugaresVotacionGeoJSON.as_view(), name='geojson'),
    url('^escuelas/(?P<pk>\d+)$', views.EscuelaDetailView.as_view(), name='detalle_escuela'),
    url('^mapa$', views.Mapa.as_view(), name='mapa'),
    url('^resultados$', views.resultados, name='resultados'),
    url('^resultados/mesa/(?P<nro>\d+)$', views.resultados_mesa, name='resultados_mesa'),
    url('^resultados/mesas$', views.resultados_mesas, name='resultados_mesas')
]
