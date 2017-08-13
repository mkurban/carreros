from django.conf.urls import url, include
from django.contrib import admin
from material.frontend import urls as frontend_urls
from elecciones import urls as elecciones_urls
from fiscales import urls as fiscales_urls
from fiscales.views import choice_home
from elecciones import views as views_elecciones

urlpatterns = [
    url(r'^$', choice_home, name="home"),
    url(r'', include(frontend_urls)),
    url(r'', include('django.contrib.auth.urls')),
    url(r'^hijack/', include('hijack.urls')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/v1/', include('api.urls', namespace='api_v1')),
    url(r'^admin/asignar_referentes/', views_elecciones.asignar_referentes,
        name='asignar-referentes'),
    url(r'^admin/', admin.site.urls),
    url(r'^elecciones/', include(elecciones_urls)),
    url(r'^fiscales/', include(fiscales_urls)),
    url(r'^attachments/', include('attachments.urls', namespace='attachments')),
]
