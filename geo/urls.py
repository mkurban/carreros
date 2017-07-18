# -*- coding: utf-8 -*-
from django.conf.urls import url, include
from django.views import generic
from . import views


urlpatterns = [
    url('^$', generic.RedirectView.as_view(url='./departamentos/'), name="index"),
    url('^admin/', generic.RedirectView.as_view(url='/admin/')),
    url('^departamentos/', include(views.DepartamentoViewSet().urls)),
    url('^localidades/', include(views.LocalidadViewSet().urls)),
]
