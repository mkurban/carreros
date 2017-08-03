# -*- coding: utf-8 -*-
from django.conf.urls import url
from . import views


urlpatterns = [
    url('^mis-contactos', views.MisContactos.as_view(), name='mis-contactos'),
    url('^mis-datos', views.MisDatos.as_view(), name='mis-datos'),
]
