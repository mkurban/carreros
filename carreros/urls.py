from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import url, include
from django.contrib import admin
from material.frontend import urls as frontend_urls
from elecciones import urls as elecciones_urls
from fiscales import urls as fiscales_urls
from fiscales.views import choice_home, QuieroSerFiscal, email, confirmar_email, exportar_emails
from elecciones import views as views_elecciones
from fiscales.forms import AuthenticationFormCustomError
from django.contrib.auth import views as auth_views


urlpatterns = [
    url(r'^$', choice_home, name="home"),
    url(r'^_email/$', email),
    url(r'^quiero-ser-fiscal/$', QuieroSerFiscal.as_view(), name='quiero-ser-fiscal'),
    url(r'^quiero-ser-fiscal/confirmar-email/(?P<uuid>[0-9a-f-]+)$', confirmar_email, name='confirmar-email'),
    url(r'^login/$', auth_views.LoginView.as_view(authentication_form=AuthenticationFormCustomError)),
    url(r'^accounts/login/$', auth_views.LoginView.as_view(authentication_form=AuthenticationFormCustomError)),

    url(r'', include(frontend_urls)),
    url(r'', include('django.contrib.auth.urls')),
    url(r'^hijack/', include('hijack.urls')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/v1/', include('api.urls', namespace='api_v1')),
    url(r'^admin/exportar-emails/', exportar_emails),
    url(r'^admin/asignar_referentes/', views_elecciones.asignar_referentes, name='asignar-referentes'),
    url(r'^admin/', admin.site.urls),
    url(r'^elecciones/', include(elecciones_urls)),
    url(r'^fiscales/', include(fiscales_urls)),
    # url(r'^attachments/', include('attachments.urls', namespace='attachments')),
    url(r'^clasificar-actas/', include('adjuntos.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)