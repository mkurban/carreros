# -*- coding: utf-8 -*-
from django.conf.urls import url
from . import views


urlpatterns = [
    url('^mis-datos$', views.MisDatos.as_view(), name='mis-datos'),
    url('^mis-contactos', views.MisContactos.as_view(), name='mis-contactos'),
    url('^donde-fiscalizo$', views.DondeFiscalizo.as_view(), name='donde-fiscalizo'),
    url('^donde-fiscalizo/estado/(?P<tipo>de_mesa|general)/(?P<pk>\d+)$',
        views.asignacion_estado, name='asignacion-estado'),
    url('^donde-fiscalizo/(?P<eleccion_id>\d+)/(?P<mesa_numero>\d+)$',
        views.MesaDetalle.as_view(), name='detalle-mesa'),
    url('^donde-fiscalizo/(?P<eleccion_id>\d+)/(?P<mesa_numero>\d+)/cargar$',
        views.cargar_resultados, name='mesa-cargar-resultados'),
    url('^donde-fiscalizo/(?P<eleccion_id>\d+)/(?P<mesa_numero>\d+)/acta$',
        views.MesaActa.as_view(), name='mesa-acta'),
    url('^donde-fiscalizo/(?P<eleccion_id>\d+)/(?P<mesa_numero>\d+)/estado/(?P<estado>\w+)$',
        views.mesa_cambiar_estado, name='mesa-cambiar-estado'),
    url('^donde-fiscalizo/(?P<eleccion_id>\d+)/(?P<mesa_numero>\d+)/fiscal/crear$',
        views.FiscalSimpleCreateView.as_view(), name='mesa-cargar-fiscal'),
    url('^donde-fiscalizo/(?P<eleccion_id>\d+)/(?P<mesa_numero>\d+)/fiscal/eliminar$',
        views.eliminar_asignacion, name='mesa-eliminar-asignacion'),
    url('^donde-fiscalizo/(?P<eleccion_id>\d+)/(?P<mesa_numero>\d+)/fiscal/editar$',
        views.FiscalSimpleUpdateView.as_view(), name='mesa-editar-fiscal'),
    url('^donde-fiscalizo/(?P<eleccion_id>\d+)/(?P<mesa_numero>\d+)/fiscal/registrar$',
        views.tengo_fiscal, name='mesa-tengo-fiscal'),
    url('^mis-datos/profile$', views.MisDatosUpdate.as_view(), name='mis-datos-update'),
    url('^mis-datos/password$', views.CambiarPassword.as_view(), name='cambiar-password'),
    url('^_confirmar/(?P<fiscal_id>\d+)$', views.confirmar_fiscal, name='confirmar-fiscal'),
]
