from django.db import models
from django.conf import settings
from django.db.models import Q
from django.contrib.contenttypes.fields import GenericRelation
from model_utils import Choices
from model_utils.models import TimeStampedModel
from django.utils import timezone
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete
from elecciones.models import desde_hasta, Mesa, LugarVotacion


class Organizacion(models.Model):
    nombre = models.CharField(max_length=100)
    referentes = models.ManyToManyField('Fiscal', related_name='es_referente_de', blank=True)

    class Meta:
        verbose_name = 'Organización'
        verbose_name_plural = 'Organizaciones'

    def __str__(self):
        return self.nombre



class Fiscal(models.Model):
    TIPO = Choices(('general', 'General'), ('de_mesa', 'de Mesa'))
    TIPO_DNI = Choices('DNI', 'CI', 'LE', 'LC')
    tipo = models.CharField(choices=TIPO, max_length=20)

    apellido = models.CharField(max_length=50)
    nombres = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200, blank=True)
    barrio = models.CharField(max_length=200, blank=True)
    localidad = models.CharField(max_length=200, blank=True)
    tipo_dni = models.CharField(choices=TIPO_DNI, max_length=3, default='DNI')
    dni = models.CharField(max_length=15)
    datos_de_contacto = GenericRelation('prensa.DatoDeContacto', related_query_name='fiscales')
    organizacion = models.ForeignKey('Organizacion', null=True, blank=True)
    user = models.OneToOneField('auth.User', null=True,
                    blank=True, related_name='fiscal',
                    on_delete=models.SET_NULL)

    class Meta:
        verbose_name_plural = 'Fiscales'
        unique_together = (('tipo_dni', 'dni'),)

    @property
    def es_general(self):
        return self.tipo == Fiscal.TIPO.general

    @property
    def telefonos(self):
        return self.datos_de_contacto.filter(tipo='teléfono').values_list('valor', flat=True)

    @property
    def emails(self):
        return self.datos_de_contacto.filter(tipo='email').values_list('valor', flat=True)

    @property
    def mesas_asignadas(self):
        if self.es_general:
            return Mesa.objects.filter(lugar_votacion__asignacion__fiscal=self).order_by('numero')
        return Mesa.objects.filter(asignacion__fiscal=self).order_by('numero')

    @property
    def escuelas(self):
        if self.es_general:
            return LugarVotacion.objects.filter(asignacion__fiscal=self)
        else:
            return LugarVotacion.objects.filter(mesas__asignacion__fiscal=self).distinct()

    @property
    def asignacion(self):
        if self.es_general:
            qs = AsignacionFiscalGeneral.objects.filter(fiscal=self)
        else:
            qs = AsignacionFiscalDeMesa.objects.filter(fiscal=self)
        return qs.last()

    @property
    def direccion_completa(self):
        return f'{self.direccion} {self.barrio}, {self.localidad}'


    def fiscales_colegas(self):
        """fiscales en la misma escuela"""
        if self.escuelas.exists():
            escuelas = self.escuelas.all()
            general = Q(tipo='general') & Q(asignacion_escuela__lugar_votacion__in=escuelas)
            de_mesa = Q(tipo='de_mesa') & Q(asignacion_mesa__mesa__lugar_votacion__in=escuelas)
            return Fiscal.objects.exclude(id=self.id).filter(general | de_mesa).order_by('-tipo')
        return Fiscal.objects.none()


    @property
    def mesas_desde_hasta(self):
        return desde_hasta(self.mesas_asignadas())

    def __str__(self):
        return f'{self.nombres} {self.apellido}'


class AsignacionFiscal(TimeStampedModel):
    ingreso = models.DateTimeField(null=True, editable=False)
    egreso = models.DateTimeField(null=True, editable=False)


    @property
    def esta_presente(self):
        if self.ingreso and not self.egreso:
            return True
        return False


    class Meta:
        abstract = True


class AsignacionFiscalDeMesa(AsignacionFiscal):
    mesa = models.ForeignKey(
        'elecciones.Mesa', related_name='asignacion')

    # es null si el fiscal general dice que la mesa está asignada
    # pero aun no hay datos.
    fiscal = models.ForeignKey('Fiscal', null=True,
        limit_choices_to={'tipo': Fiscal.TIPO.de_mesa}, related_name='asignacion_mesa')

    def __str__(self):
        if self.fiscal:
            return f'Asignacion {self.mesa}: {self.fiscal}'
        return f'Asignación {self.mesa}: registro sin datos'

    class Meta:
        verbose_name = 'Asignación de Fiscal de Mesa'
        verbose_name_plural = 'Asignaciones de Fiscal de Mesa'


class AsignacionFiscalGeneral(AsignacionFiscal):
    lugar_votacion = models.ForeignKey(
        'elecciones.LugarVotacion', related_name='asignacion')
    fiscal = models.ForeignKey('Fiscal',
        limit_choices_to={'tipo': Fiscal.TIPO.general},
        related_name='asignacion_escuela'
    )


    def __str__(self):
        return f'{self.fiscal} {self.lugar_votacion}'

    class Meta:
        verbose_name = 'Asignación de Fiscal General'
        verbose_name_plural = 'Asignaciones de Fiscal General'



@receiver(post_save, sender=Fiscal)
def crear_user_para_fiscal(sender, instance=None, created=False, **kwargs):
    if created and not instance.user:
        user = User(
            username=instance.dni,
            first_name=instance.nombres,
            last_name=instance.apellido,
            is_active=True,
        )
        if instance.emails:
            user.email = instance.emails[0]
        user.set_password(settings.DEFAULT_PASS_PREFIX + instance.dni[-3:])
        user.save()
        instance.user = user
        instance.save(update_fields=['user'])



@receiver(pre_delete, sender=Fiscal)
def borrar_user_para_fiscal(sender, instance=None, **kwargs):
    if instance.user:
        instance.user.delete()
