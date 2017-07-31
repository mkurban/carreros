from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum
from django.conf import settings


class Seccion(models.Model):
    numero = models.PositiveIntegerField()
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class Circuito(models.Model):
    seccion = models.ForeignKey(Seccion)
    numero = models.CharField(max_length=10)
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return f"Circuito {self.numero} - {self.nombre}"


class LugarVotacion(models.Model):
    circuito = models.ForeignKey(Circuito)
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=100)
    barrio = models.CharField(max_length=100, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    geo = models.CharField(max_length=200, blank=True)
    calidad = models.CharField(max_length=20, help_text='calidad de la geolocalizacion', editable=False, blank=True)
    electores = models.PositiveIntegerField()
    latitud = models.DecimalField(null=True, decimal_places=7, max_digits=10)
    longitud = models.DecimalField(null=True, decimal_places=7, max_digits=10)


    def __str__(self):
        return f"{self.nombre} - {self.circuito}"


class Mesa(models.Model):
    numero = models.PositiveIntegerField()
    circuito = models.ForeignKey(Circuito)  #
    lugar_votacion = models.ForeignKey(LugarVotacion, verbose_name='Lugar de votacion', null=True)
    url = models.URLField(blank=True, help_text='url al telegrama')

    @property
    def computados(self):
        return self.votomesaoficial_set.aggregate(Sum('votos'))['votos__sum']

    def __str__(self):
        return f"Mesa {self.numero} - {self.circuito}"


class Partido(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class Opcion(models.Model):
    dne_id = models.PositiveIntegerField(primary_key=True)
    nombre = models.CharField(max_length=100)
    partido = models.ForeignKey(Partido, null=True)   # blanco, / recurrido / etc

    def __str__(self):
        return f'{self.partido} - {self.nombre}'


class Eleccion(models.Model):
    nombre = models.CharField(max_length=50)
    fecha = models.DateTimeField(blank=True, null=True)
    opciones = models.ManyToManyField(Opcion)

    def __unicode__(self):
        return self.nombre


class AbstractVotoMesa(models.Model):
    eleccion = models.ForeignKey(Eleccion)
    mesa = models.ForeignKey(Mesa)
    opcion = models.ForeignKey(Opcion)
    votos = models.IntegerField()

    class Meta:
        abstract = True
        unique_together = ('eleccion', 'mesa', 'opcion')


    def __str__(self):
        return f"{self.eleccion} - {self.opcion}: {self.votos}"


class VotoMesaReportado(AbstractVotoMesa):
    usuario = models.ForeignKey(User)


class VotoMesaOficial(AbstractVotoMesa):
    pass
