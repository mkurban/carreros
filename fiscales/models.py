from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from model_utils import Choices
from model_utils.models import TimeStampedModel
from django.utils import timezone
from elecciones.models import desde_hasta, Mesa


class Organizacion(models.Model):
    nombre = models.CharField(max_length=100)
    referentes = models.ManyToManyField('Fiscal', 'referentes_de_la_orga')

    class Meta:
        verbose_name = 'Organización'
        verbose_name_plural = 'Organizaciones'


class Fiscal(models.Model):
    TIPO = Choices(('general', 'General'), ('de_mesa', 'de Mesa'))
    TIPO_DNI = Choices('DNI', 'CI', 'LE', 'LC')
    tipo = models.CharField(choices=TIPO, max_length=20)

    apellido = models.CharField(max_length=50)
    nombres = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200, blank=True)
    localidad = models.CharField(max_length=200, blank=True)
    tipo_dni = models.CharField(choices=TIPO_DNI, max_length=3, default='DNI')
    dni = models.CharField(max_length=15)
    datos_de_contacto = GenericRelation('prensa.DatoDeContacto', related_query_name='fiscales')
    organizacion = models.ForeignKey('Organizacion', null=True, blank=True)
    user = models.ForeignKey('auth.User', null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Fiscales'
        unique_together = (('tipo_dni', 'dni'),)

    @property
    def es_general(self):
        return self.tipo == Fiscal.TIPO.general

    @property
    def telefonos(self):
        return ' / '.join(self.datos_de_contacto.filter(tipo='teléfono').values_list('valor', flat=True))

    @property
    def emails(self):
        return ' / '.join(self.datos_de_contacto.filter(tipo='email').values_list('valor', flat=True))

    def mesas_asignadas(self):
        if self.es_general:
            return Mesa.objects.filter(lugar_votacion__fiscal_general__fiscal=self).order_by('numero')
        return Mesa.objects.filter(asignacion_fiscales__fiscal=self).order_by('numero')

    @property
    def mesas_desde_hasta(self):
        return desde_hasta(self.mesas_asignadas)

    def __str__(self):
        return f'{self.nombres} {self.apellido}'


class AsignacionFiscal(TimeStampedModel):
    ingreso = models.DateTimeField(null=True, editable=False)
    egreso = models.DateTimeField(null=True, editable=False)

    class Meta:
        abstract = True

    @property
    def esta_presente(self):
        if self.ingreso and not self.egreso:
            return False
        if ingreso <  timezone.now():
            return True
        return False


class AsignacionFiscalDeMesa(AsignacionFiscal):
    mesa = models.ForeignKey(
        'elecciones.Mesa', related_name='asignacion_fiscales')
    fiscal = models.ForeignKey('Fiscal',
        limit_choices_to={'tipo': Fiscal.TIPO.de_mesa}, related_name='asignacion_mesa')


    def __str__(self):
        return f'{self.fiscal} {self.mesa}'


    class Meta:
        verbose_name = 'Asignación de Fiscal de Mesa'
        verbose_name_plural = 'Asignaciones de Fiscal de Mesa'


class AsignacionFiscalGeneral(AsignacionFiscal):
    lugar_votacion = models.ForeignKey(
        'elecciones.LugarVotacion', related_name='fiscal_general')
    fiscal = models.ForeignKey('Fiscal',
        limit_choices_to={'tipo': Fiscal.TIPO.general},
        related_name='asignacion_escuela'
    )


    def __str__(self):
        return f'{self.fiscal} {self.lugar_votacion}'

    class Meta:
        verbose_name = 'Asignación de Fiscal General'
        verbose_name_plural = 'Asignaciones de Fiscal General'
