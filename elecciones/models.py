import os
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import models
from django.db.models import Sum
from django.conf import settings
from djgeojson.fields import PointField
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from model_utils.fields import StatusField, MonitorField
from model_utils import Choices


def desde_hasta(qs):
    qs = qs.values_list('numero', flat=True).order_by('numero')
    inicio, fin = qs.first(), qs.last()
    if inicio == fin:
        return inicio
    return f'{inicio} - {fin}'


class Seccion(models.Model):
    numero = models.PositiveIntegerField()
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Sección electoral'
        verbose_name_plural = 'Secciones electorales'

    def __str__(self):
        return f"{self.numero} - {self.nombre}"


class Circuito(models.Model):
    seccion = models.ForeignKey(Seccion)
    numero = models.CharField(max_length=10)
    nombre = models.CharField(max_length=100)
    referentes = models.ManyToManyField('fiscales.Fiscal',
        related_name='es_referente_de_circuito',
        blank=True
    )

    class Meta:
        verbose_name = 'Circuito electoral'
        verbose_name_plural = 'Circuitos electorales'
        ordering = ('numero',)

    def __str__(self):
        return f"{self.numero} - {self.nombre}"


class LugarVotacion(models.Model):
    circuito = models.ForeignKey(Circuito)
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=100)
    barrio = models.CharField(max_length=100, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    geo = models.CharField(max_length=200, blank=True)
    calidad = models.CharField(max_length=20, help_text='calidad de la geolocalizacion', editable=False, blank=True)
    electores = models.PositiveIntegerField()
    geom = PointField(null=True)

    # denormalizacion para hacer queries más simples
    latitud = models.FloatField(null=True, editable=False)
    longitud = models.FloatField(null=True, editable=False)

    class Meta:
        verbose_name = 'Lugar de votación'
        verbose_name_plural = "Lugares de votación"

    def save(self, *args, **kwargs):

        if self.geom:
            self.longitud, self.latitud = self.geom['coordinates']
        else:
            self.longitud, self.latitud = None, None
        super().save(*args, **kwargs)

    @property
    def coordenadas(self):
        return f'{self.latitud},{self.longitud}'

    @property
    def direccion_completa(self):
        return f'{self.direccion} {self.barrio} {self.ciudad}'

    @property
    def mesas_desde_hasta(self):
        return desde_hasta(self.mesas)

    @property
    def asignacion_actual(self):
        return self.asignacion.order_by('-ingreso').last()

    def __str__(self):
        return f"{self.nombre} - {self.circuito}"


def path_foto_acta(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    _, ext = os.path.splitext(filename)
    return '{}/{}/{}{}'.format(
        instance.circuito.seccion.numero,
        instance.circuito.numero,
        instance.numero,
        ext
    )


class Mesa(models.Model):
    ESTADOS_ = ('EN ESPERA', 'ABIERTA', 'CERRADA', 'ESCRUTADA')
    ESTADOS = Choices(*ESTADOS_)

    estado = StatusField(choices_name='ESTADOS', default='EN ESPERA')
    hora_abierta = MonitorField(monitor='estado', when=['ABIERTA'])
    hora_cerrada = MonitorField(monitor='estado', when=['CERRADA'])
    hora_escrutada = MonitorField(monitor='estado', when=['ESCRUTADA'])

    numero = models.PositiveIntegerField()
    es_testigo = models.BooleanField(default=False)
    circuito = models.ForeignKey(Circuito)  #
    lugar_votacion = models.ForeignKey(LugarVotacion, verbose_name='Lugar de votacion', null=True, related_name='mesas')
    url = models.URLField(blank=True, help_text='url al telegrama')
    foto_del_acta = models.ImageField(upload_to=path_foto_acta, null=True, blank=True)


    def get_absolute_url(self):
        return reverse('detalle-mesa', args=(self.numero,))

    @property
    def asignacion_actual(self):
        return self.asignacion.order_by('-ingreso').last()

    @property
    def computados(self):
        return self.votomesaoficial_set.aggregate(Sum('votos'))['votos__sum']

    @property
    def proximo_estado(self):
        if self.estado == 'ESCRUTADA':
            return self.estado
        list(Mesa.ESTADOS)
        pos = Mesa.ESTADOS_.index(self.estado)
        return Mesa.ESTADOS_[pos + 1]


    def __str__(self):
        return f"Mesa {self.numero}"


class Partido(models.Model):
    orden = models.PositiveIntegerField(help_text='Orden opcion')
    numero = models.PositiveIntegerField()
    nombre = models.CharField(max_length=100)
    ordering = ['orden']


    def __str__(self):
        return self.nombre


class Opcion(models.Model):
    orden = models.PositiveIntegerField(help_text='Orden en el acta')
    nombre = models.CharField(max_length=100)
    partido = models.ForeignKey(Partido, null=True, blank=True)   # blanco, / recurrido / etc
    orden = models.PositiveIntegerField(
        help_text='Orden en la boleta', null=True, blank=True)


    class Meta:
        verbose_name = 'Opción'
        verbose_name_plural = 'Opciones'
        ordering = ['orden']



    def __str__(self):
        if self.partido:
            return f'{self.partido} - {self.nombre}'
        return self.nombre

class Eleccion(models.Model):
    nombre = models.CharField(max_length=50)
    fecha = models.DateTimeField(blank=True, null=True)
    opciones = models.ManyToManyField(Opcion)

    @classmethod
    def opciones_actuales(cls):
        if cls.objects.last():
            return cls.objects.last().opciones.all()
        return Opcion.objects.none()

    class Meta:
        verbose_name = 'Elección'
        verbose_name_plural = 'Elecciones'

    def __str__(self):
        return self.nombre


class AbstractVotoMesa(models.Model):
    eleccion = models.ForeignKey(Eleccion)
    mesa = models.ForeignKey(Mesa)
    opcion = models.ForeignKey(Opcion)
    votos = models.PositiveIntegerField()

    class Meta:
        abstract = True
        unique_together = ('eleccion', 'mesa', 'opcion')


    def __str__(self):
        return f"{self.eleccion} - {self.opcion}: {self.votos}"


class VotoMesaReportado(AbstractVotoMesa):
    fiscal = models.ForeignKey('fiscales.Fiscal')



class VotoMesaOficial(AbstractVotoMesa):
    pass
