from material.frontend.views import ModelViewSet
from . import models


class LocalidadViewSet(ModelViewSet):
    model = models.Localidad
    # list_display = ('nombre', 'departamento', 'poblacion')


class DepartamentoViewSet(ModelViewSet):
    model = models.Departamento
    # list_display = ('nombre', 'poblacion')
