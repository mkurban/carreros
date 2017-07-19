# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url, include
from django.views import generic

from . import views


urlpatterns = [
    url('^$', generic.RedirectView.as_view(url='./personas/'), name="index"),
    url('^personas/', include(views.PersonaViewSet().urls)),
    url('^medios/', include(views.MedioViewSet().urls)),
    url('^programas/', include(views.ProgramaViewSet().urls)),

]