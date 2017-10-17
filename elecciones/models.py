import os
from itertools import chain
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import models
from django.db.models import Sum, IntegerField, Case, Value, When, F
from django.conf import settings
from djgeojson.fields import PointField
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.dispatch import receiver
from django.db.models.signals import m2m_changed, post_save
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
    circuito = models.ForeignKey(Circuito, related_name='escuelas')
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=100)
    barrio = models.CharField(max_length=100, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    calidad = models.CharField(max_length=20, help_text='calidad de la geolocalizacion', editable=False, blank=True)
    electores = models.PositiveIntegerField(null=True, blank=True)
    geom = PointField(null=True)

    # denormalizacion para hacer queries más simples
    latitud = models.FloatField(null=True, editable=False)
    longitud = models.FloatField(null=True, editable=False)

    class Meta:
        verbose_name = 'Lugar de votación'
        verbose_name_plural = "Lugares de votación"


    def get_absolute_url(self):
        url = reverse('donde-fiscalizo')
        return f'{url}#donde{self.id}'


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
    def asignaciones(self):
        return self.asignacion.exclude(fiscal__es_referente_de_circuito__isnull=False)

    @property
    def asignacion_actual(self):
        return self.asignacion.exclude(fiscal__es_referente_de_circuito__isnull=False).order_by('-ingreso', '-id').last()

    @property
    def mesas_actuales(self):
        return self.mesas.filter(eleccion=Eleccion.actual())

    @property
    def color(self):
        if self.mesa_testigo:
            return 'blue'
        if not self.asignacion.exists():
            return 'red'
        elif self.asignacion.filter(ingreso__isnull=False).exists():
            return 'green'
        return 'orange'

    @property
    def seccion(self):
        return str(self.circuito.seccion)

    @property
    def mesa_testigo(self):
        return self.mesas.filter(eleccion__id=3, es_testigo=True).first()


    @property
    def resultados_oficiales(self):
        return VotoMesaOficial.objects.filter(mesa__lugar_votacion=self, opcion__id__in=Opcion.MOSTRABLES).aggregate(
            **Opcion.AGREGACIONES
        )


    def __str__(self):
        return f"{self.nombre} - {self.circuito}"


def path_foto_acta(instance, filename):
    # file will be uploaded to MEDIA_ROOT/
    _, ext = os.path.splitext(filename)
    return 'actas/{}/{}{}'.format(
        instance.eleccion.slug,
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

    eleccion = models.ForeignKey('Eleccion')
    numero = models.PositiveIntegerField()
    es_testigo = models.BooleanField(default=False)
    circuito = models.ForeignKey(Circuito)  #
    lugar_votacion = models.ForeignKey(LugarVotacion, verbose_name='Lugar de votacion', null=True, related_name='mesas')
    url = models.URLField(blank=True, help_text='url al telegrama')
    electores = models.PositiveIntegerField(null=True, blank=True)
    taken = models.DateTimeField(null=True, editable=False)


    def get_absolute_url(self):
        return reverse('detalle-mesa', args=(self.eleccion.id, self.numero,))

    @property
    def asignacion_actual(self):
        return self.asignacion.order_by('-ingreso').last()

    @property
    def computados(self):
        return self.votomesaoficial_set.aggregate(Sum('votos'))['votos__sum']

    @property
    def tiene_reporte(self):
        return self.votomesareportado_set.aggregate(Sum('votos'))['votos__sum']

    @property
    def foto_del_acta(self):
        from adjuntos.models import Attachment
        try:
            return self.attachment.foto
        except Attachment.DoesNotExist:
            return None

    @property
    def proximo_estado(self):
        if self.estado == 'ESCRUTADA':
            return self.estado
        pos = Mesa.ESTADOS_.index(self.estado)
        return Mesa.ESTADOS_[pos + 1]

    def __str__(self):
        return f"Mesa {self.numero}"


class Partido(models.Model):
    orden = models.PositiveIntegerField(help_text='Orden opcion')
    numero = models.PositiveIntegerField(null=True, blank=True)
    nombre = models.CharField(max_length=100)
    nombre_corto = models.CharField(max_length=10, default='')
    color = models.CharField(max_length=30, default='', blank=True)
    referencia = models.CharField(max_length=30, default='', blank=True)
    ordering = ['orden']


    def __str__(self):
        return self.nombre


class Opcion(models.Model):
    MOSTRABLES = list(range(1, 21))
    AGREGACIONES = {f'{id}': Sum(Case(When(opcion__id=id, then=F('votos')),
                             output_field=IntegerField())) for id in MOSTRABLES}

    orden = models.PositiveIntegerField(help_text='Orden en el acta')
    nombre = models.CharField(max_length=100)
    nombre_corto = models.CharField(max_length=10, default='')
    partido = models.ForeignKey(Partido, null=True, blank=True)   # blanco, / recurrido / etc
    orden = models.PositiveIntegerField(
        help_text='Orden en la boleta', null=True, blank=True)
    obligatorio = models.BooleanField(default=False)
    es_contable = models.BooleanField(default=True)
    codigo_dne = models.PositiveIntegerField(null=True, blank=True, help_text='Nº de lista')
    codigo_dne = models.PositiveIntegerField(null=True, blank=True, help_text='Nº asignado en la base de datos de resultados oficiales')


    class Meta:
        verbose_name = 'Opción'
        verbose_name_plural = 'Opciones'
        ordering = ['orden']

    def __str__(self):
        if self.partido:
            return f'{self.partido} - {self.nombre}'
        return self.nombre


class Eleccion(models.Model):
    slug = models.SlugField(max_length=50, unique=True)
    nombre = models.CharField(max_length=50)
    fecha = models.DateTimeField(blank=True, null=True)
    opciones = models.ManyToManyField(Opcion)

    @classmethod
    def opciones_actuales(cls):
        e = cls.actual()
        if e:
            return e.opciones.all()
        return Opcion.objects.none()

    @classmethod
    def actual(cls):
        actual = cls.objects.order_by('-id').first()
        return actual

    class Meta:
        verbose_name = 'Elección'
        verbose_name_plural = 'Elecciones'

    def __str__(self):
        return self.nombre


class AbstractVotoMesa(models.Model):
    mesa = models.ForeignKey(Mesa)
    opcion = models.ForeignKey(Opcion)
    votos = models.PositiveIntegerField(null=True)

    class Meta:
        abstract = True
        unique_together = ('mesa', 'opcion')


    def __str__(self):
        return f"{self.mesa} - {self.opcion}: {self.votos}"


class VotoMesaReportado(AbstractVotoMesa):
    fiscal = models.ForeignKey('fiscales.Fiscal')



class VotoMesaOficial(AbstractVotoMesa):
    pass


@receiver(m2m_changed, sender=Circuito.referentes.through)
def referentes_cambiaron(sender, instance, action, reverse,
                         model, pk_set, using, **kwargs):
    """cuando se asigna a un circuito, se crean las asignaciones
    a todas las escuelas del circuito"""

    from fiscales.models import AsignacionFiscalGeneral, Fiscal   # avoid circular import
    eleccion = Eleccion.actual()
    if action == 'post_remove':
        # quitar a estos fiscales cualquier asignacion a escuelas del circuito
        AsignacionFiscalGeneral.objects.filter(eleccion=eleccion,
            lugar_votacion__circuito=instance, fiscal__id__in=pk_set).delete()
    elif action == 'post_add':
        fiscales = Fiscal.objects.filter(id__in=pk_set)
        escuelas = LugarVotacion.objects.filter(circuito=instance)
        for fiscal in fiscales:
            for escuela in escuelas:
                AsignacionFiscalGeneral.objects.create(eleccion=eleccion, lugar_votacion=escuela, fiscal=fiscal)
