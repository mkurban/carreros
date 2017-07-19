from django.db import models
from model_utils import Choices


class Departamento(models.Model):
    nombre = models.CharField(max_length=50)
    poblacion = models.PositiveIntegerField('Población')

    def __str__(self):
        return self.nombre


class Localidad(models.Model):
    TIPO_LOCALIDAD = Choices('Urbana', 'Rural')
    nombre = models.CharField(max_length=50)
    departamento = models.ForeignKey(Departamento)
    poblacion = models.PositiveIntegerField('Población')
    tipo = models.CharField(choices=TIPO_LOCALIDAD, max_length=50)

    def __str__(self):
        return f'{self.nombre} ({self.departamento})'
