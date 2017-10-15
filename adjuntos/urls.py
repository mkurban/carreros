from django.conf.urls import url
from .views import elegir_adjunto, AsignarMesaAdjunto

urlpatterns = [
    url(r'^$', elegir_adjunto, name="elegir-adjunto"),
    url(r'^(?P<attachment_id>\d+)/$', AsignarMesaAdjunto.as_view(), name='asignar-mesa'),
]
