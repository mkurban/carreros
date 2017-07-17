from django.db import models
from model_utils import Choices
# Create your models here.


class Eleccion(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    fecha = models.DateField()


class Lista(models.Model):
    # eleccion = models.ForeignKey(Eleccion)
    nombre = models.CharField(max_length=50, unique=True)
    numero = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return self.nombre


class Candidato(models.Model):
    CARGOS = Choices('Diputado Nacional', 'Senador Nacional')
    TIPO = Choices('Titular', 'Suplente')
    lista = models.ForeignKey(Lista)
    apellido = models.CharField(max_length=50)
    nombres = models.CharField(max_length=100)
    candidatura_a = models.CharField(choices=CARGOS, max_length=50, default='Diputado Nacional')
    tipo = models.CharField(choices=TIPO, max_length=20)
    posicion = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.nombres} {self.apellido}'

    class Meta:
        unique_together = (('lista', 'candidatura_a', 'posicion'),)

