from django.db import models
from model_utils import Choices


class Departamento(models.Model):
    nombre = models.CharField(max_length=50)
    poblacion = models.PositiveIntegerField('Población')


class Localidad(models.Model):
    TIPO_LOCALIDAD = Choices('Urbana', 'Rural')
    nombre = models.CharField(max_length=50)
    poblacion = models.PositiveIntegerField('Población')
    tipo = models.CharField(choices=TIPO_LOCALIDAD, max_length=50)
