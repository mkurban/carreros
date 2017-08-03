"""carreros URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.views import generic
from django.contrib import admin
from material.frontend import urls as frontend_urls
from elecciones import urls as elecciones_urls
from fiscales import urls as fiscales_urls
from fiscales.views import choice_home

urlpatterns = [
    url(r'^$', choice_home, name="home"),
    url(r'', include(frontend_urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/v1/', include('api.urls', namespace='api_v1')),
    url(r'^admin/', admin.site.urls),
    url(r'^elecciones/', include(elecciones_urls)),
    url(r'^fiscales/', include(fiscales_urls)),
    url(r'^attachments/', include('attachments.urls', namespace='attachments')),

]
