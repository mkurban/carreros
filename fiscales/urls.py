# -*- coding: utf-8 -*-
from django.conf.urls import url
from . import views


urlpatterns = [
    url('^mis-datos$', views.MisDatos.as_view(), name='mis-datos'),
    url('^mis-contactos', views.MisContactos.as_view(), name='mis-contactos'),
    url('^donde-fiscalizo$', views.DondeFiscalizo.as_view(), name='donde-fiscalizo'),
    url('^donde-fiscalizo/(?P<mesa_numero>\d+)', views.MesaDetalle.as_view(), name='detalle-mesa'),
    url('^mis-datos/profile$', views.MisDatosUpdate.as_view(), name='mis-datos-update'),
    url('^mis-datos/password$', views.CambiarPassword.as_view(), name='cambiar-password'),
]
