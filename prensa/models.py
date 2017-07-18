from django.db import models
from model_utils import Choices
from taggit.managers import TaggableManager

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType


class DatoDeContacto(models.Model):
    """Modelo generérico para guardar datos de contacto de personas o medios"""

    TIPOS = Choices(
        'email', 'teléfono', 'web', 'twitter', 'facebook',
        'instagram', 'youtube', 'skype'
    )


    tipo = models.CharField(choices=TIPOS, max_length=20)
    valor = models.CharField(max_length=100)
    # generic relation
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f'{self.tipo}: {self.valor}'


class Persona(models.Model):
    RELACIONES = Choices('AMIGX', 'COMPAÑERX', 'INDIFERENTE', 'OPOSITXR')

    apellido = models.CharField(max_length=100)
    nombres = models.CharField(max_length=100)
    relacion = models.CharField(choices=RELACIONES, max_length=20)
    datos_de_contacto = GenericRelation('DatoDeContacto', related_query_name='personas')
    localidad = models.ForeignKey('geo.Localidad', null=True, blank=True)
    fuente = models.ForeignKey('auth.User', null=True, blank=True)

    def __str__(self):
        return f'{self.nombres} {self.apellido}'


class Medio(models.Model):
    TIPO_DE_MEDIO = Choices('Radio', 'Televisión', 'Gráfica', 'Via Publica', 'Web', 'Redes sociales')
    nombre = models.CharField('Nombre del medio', max_length=50)
    tipo = models.CharField(choices=TIPO_DE_MEDIO, max_length=50)
    direccion = models.CharField('Dirección', max_length=50)
    localidad = models.ForeignKey('geo.Localidad')
    datos_de_contacto = GenericRelation(DatoDeContacto, related_query_name='medios')
    detalles_tecnicos = models.TextField(blank=True, null=True)
    fuente = models.ForeignKey('auth.User', null=True, blank=True)

    def __str__(self):
        return f'{self.nombre} ({self.tipo})'


class Rol(models.Model):
    ROLES = Choices('Conductor/a', 'Periodista', 'Productor/a', 'Técnico/a', 'Contacto')
    persona = models.ForeignKey('Persona')
    programa = models.ForeignKey('Programa')
    rol = models.CharField(choices=ROLES, max_length=50, blank=True)
    es_contacto = models.BooleanField(default=False)


class Programa(models.Model):
    nombre = models.CharField('Nombre del programa o sección', max_length=150)
    medio = models.ForeignKey('Medio')
    staff = models.ManyToManyField('Persona', related_name='programas_realizados', through='Rol')

    # TODO ver django-scheduler u otra app para modelar la recurrencia
    # y poder filtrar programas en un periodo de tiempo
    detalles = models.TextField(help_text='Dias, horarios, comentarios, etc')

    def __str__(self):
        return f'{self.nombre} - {self.medio}'


class Aparicion(models.Model):
    programa = models.ForeignKey('Programa')
    candidatos = models.ManyToManyField('candidatos.Candidato', related_name='apariciones_en_medios')
    fecha = models.DateTimeField()
    minuta = models.TextField(help_text='Qué se dijo/mostró?', blank=True)
    tags = TaggableManager(help_text='Palabras clave separadas por coma. Ejemplo: entrevista, trayectoria, lucha gremial')

    def __str__(self):
        return f'{self.programa} - {self.fecha}'