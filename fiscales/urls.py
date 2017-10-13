# -*- coding: utf-8 -*-
from django.conf.urls import url
from . import views


urlpatterns = [
    url('^mis-datos$', views.MisDatos.as_view(), name='mis-datos'),
    url('^mis-contactos', views.MisContactos.as_view(), name='mis-contactos'),
    url('^mis-voluntarios', views.MisVoluntarios.as_view(), name='mis-voluntarios'),
    url('^$', views.DondeFiscalizo.as_view(), name='donde-fiscalizo'),
    url('^estado/(?P<tipo>de_mesa|general)/(?P<pk>\d+)$',
        views.asignacion_estado, name='asignacion-estado'),
    url('^(?P<eleccion_id>\d+)/(?P<mesa_numero>\d+)$',
        views.MesaDetalle.as_view(), name='detalle-mesa'),
    url('^(?P<eleccion_id>\d+)/(?P<mesa_numero>\d+)/cargar$',
        views.cargar_resultados, name='mesa-cargar-resultados'),
    url('^(?P<eleccion_id>\d+)/(?P<mesa_numero>\d+)/acta$',
        views.MesaActa.as_view(), name='mesa-acta'),
    url('^(?P<eleccion_id>\d+)/(?P<mesa_numero>\d+)/estado/(?P<estado>\w+)$',
        views.mesa_cambiar_estado, name='mesa-cambiar-estado'),

    url('^(?P<eleccion_id>\d+)/m(?P<mesa_numero>\d+)/fiscal/asignar$',
        views.AsignarFiscalView.as_view(), {'tipo': 'de_mesa'}, name='mesa-asignar-fiscal'),
    url('^(?P<eleccion_id>\d+)/m(?P<mesa_numero>\d+)/fiscal/crear$',
        views.FiscalSimpleCreateView.as_view(), {'tipo': 'de_mesa'}, name='mesa-cargar-fiscal'),
    url('^(?P<eleccion_id>\d+)/m(?P<mesa_numero>\d+)/fiscal/eliminar$',
        views.eliminar_asignacion, {'tipo': 'de_mesa'}, name='mesa-eliminar-asignacion'),
    url('^(?P<eleccion_id>\d+)/m(?P<mesa_numero>\d+)/fiscal/editar$',
        views.FiscalSimpleUpdateView.as_view(), {'tipo': 'de_mesa'}, name='mesa-editar-fiscal'),
    url('^(?P<eleccion_id>\d+)/m(?P<mesa_numero>\d+)/fiscal/registrar$',
        views.tengo_fiscal, name='mesa-tengo-fiscal'),

    url('^(?P<eleccion_id>\d+)/e(?P<escuela_id>\d+)/fiscal/crear$',
        views.AsignarFiscalView.as_view(), {'tipo': 'general'}, name='escuela-asignar-fiscal'),
    url('^(?P<eleccion_id>\d+)/e(?P<escuela_id>\d+)/fiscal/crear$',
        views.FiscalSimpleCreateView.as_view(), {'tipo': 'general'}, name='escuela-cargar-fiscal'),
    url('^(?P<eleccion_id>\d+)/e(?P<escuela_id>\d+)/fiscal/eliminar$',
        views.eliminar_asignacion, {'tipo': 'general'}, name='escuela-eliminar-asignacion'),
    url('^(?P<eleccion_id>\d+)/e(?P<escuela_id>\d+)/fiscal/editar$',
        views.FiscalSimpleUpdateView.as_view(), {'tipo': 'general'}, name='escuela-editar-fiscal'),


    url('^mis-datos/profile$', views.MisDatosUpdate.as_view(), name='mis-datos-update'),
    url('^mis-datos/password$', views.CambiarPassword.as_view(), name='cambiar-password'),
    url('^_confirmar/(?P<fiscal_id>\d+)$', views.confirmar_fiscal, name='confirmar-fiscal'),
]
