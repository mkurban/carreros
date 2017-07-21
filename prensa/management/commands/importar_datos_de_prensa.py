import re
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from nameparser import HumanName
from pyexcel_io.exceptions import NoSupportingPluginFound
from pyexcel_xlsx import get_data
from prensa.models import Persona, Medio, Programa, Rol
from prensa.forms import DatoDeContactoModelForm
from geo.models import Localidad


LUIS = User.objects.get(username='luis')


def apellido_nombres(raw):
    nombre = HumanName(raw)
    apellido = nombre.last
    nombres = f'{nombre.first}'
    if nombre.middle:
        nombres += f' {nombre.middle}'
    return apellido, nombres



class Command(BaseCommand):
    HOJAS = ['Programa  Sección', 'Medios', 'Personas']

    help = "Importa base de prensa en XLSX exportada de gdocs"

    def add_arguments(self, parser):
        parser.add_argument('xlsx')

    def success(self, msg):
        self.stdout.write(self.style.SUCCESS(msg))

    def warning(self, msg):
        self.stdout.write(self.style.WARNING(msg))


    @staticmethod
    def _parsear_contactos(raw):
        raw = raw or ''
        raw = raw.replace('-', ' ')
        emails = re.findall(r'[\w\.-]+@[\w\.-]+', raw)
        telefonos = re.findall(r'(?:^|\s)(0?\d+[\s\-]?\d+|[45]\d+|15\d+)', raw)
        urls = re.findall(r'https?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', raw)
        return {'email': emails, 'teléfono': telefonos, 'web': urls}

    def load_dato_de_contacto(self, datos_de_contacto, objeto):
        ct = ContentType.objects.get(app_label='prensa', model=type(objeto).__name__.lower())
        for tipo, valores in datos_de_contacto.items():
            for valor in valores:
                d = DatoDeContactoModelForm({
                    'tipo': tipo,
                    'valor': valor,
                    'content_type': ct.id,
                    'object_id': objeto.id
                })
                if d.is_valid():
                    dato = d.save()
                    self.success(f'Importado {dato} para {objeto}')
                else:
                    self.warning(f'Ignorado {d.errors}')


    def load_medios(self, medios_data):

        keys = ['nombre', 'tipo', 'detalles_tecnicos',
                'datos_de_contacto', 'direccion', 'localidad', 'fuente']

        ct = ContentType.objects.get(app_label='prensa', model='medio')
        for row in medios_data[1:]:
            data = dict(zip(keys, row))
            datos_de_contacto = data.pop('datos_de_contacto')
            datos_de_contacto = Command._parsear_contactos(datos_de_contacto)

            localidad = data.get('localidad')

            if not data['tipo']:
                self.warning(f"{data['nombre']} sin tipo. Asume TV")
                data['tipo'] = 'TELEVISION'

            data['direccion'] = data.get('direccion', '') or ''
            data['detalles_tecnicos'] = data.get('detalles_tecnicos', '') or ''

            if localidad:
                try:
                    data['localidad'] = Localidad.objects.get(nombre=localidad)
                except Localidad.DoesNotExist:
                    self.warning(f'{localidad} no existe')
                    data['localidad'] = None

            medio, created = Medio.objects.get_or_create(**data)
            if not created:
                self.warning(f'{medio} ya existe')
            else:
                self.success(f'Creado {medio}')
                self.load_dato_de_contacto(datos_de_contacto, medio)


    def load_personas(self, data_personas):
        p = {}
        for row in data_personas[1:]:

            apellido, nombres = apellido_nombres(row[0])
            # contactos
            raw_data = f'{row[1]} {row[2]} {row[3]}'
            info_contacto = Command._parsear_contactos(raw_data)

            p['relacion'] = row[4] or ''
            try:
                comentario = row[5] or ''
                p['comentarios'] = f'Referente / Organización / Medio: {comentario}' if comentario else ''
                p['fuente'] = row[6] or ''
            except IndexError:
                pass

            persona, created = Persona.objects.get_or_create(
                apellido=apellido, nombres=nombres, defaults=p)
            if not created:
                self.warning(f'{persona} ya existe')
            else:
                self.success(f'Creado {persona}')
                self.load_dato_de_contacto(info_contacto, persona)

    def load_programas(self, data_programas):
        p = {}
        for row in data_programas[1:]:
            if not row[0]:
                continue
            p['medio'] = Medio.objects.get(nombre=row[0])
            try:
                p['nombre'] = row[3] or '-'
            except IndexError:
                continue

            p['detalles'] = row[5] or ''
            try:
                p['fuente'] = row[9]  or ''
            except IndexError:
                p['fuente'] = ''

            programa, created = Programa.objects.get_or_create(**p)

            if not created:
                self.warning(f'{programa} ya existe')
            else:
                self.success(f'Creado {programa}')
                for contacto in row[6:9]:
                    if contacto:
                        try:
                            apellido, nombres = apellido_nombres(contacto)
                            persona = Persona.objects.get(
                                apellido=apellido, nombres=nombres
                            )
                        except Persona.DoesNotExist:
                            # contacto invalido
                            self.warning(f'{contacto} es invalido')
                            continue
                        if contacto == row[4]:
                            # periodista
                            rol = 'Periodista'
                        else:
                            rol = 'Contacto'

                        Rol.objects.create(
                            rol=rol, persona=persona, programa=programa,
                            es_contacto=True)

                        self.success(f'Asociado {persona} a {programa}')

    def handle(self, *args, **options):

        path = options['xlsx']
        try:
            data = get_data(path)
            assert list(data.keys())[:3] == Command.HOJAS
        except (AssertionError, NoSupportingPluginFound):
            raise CommandError('Archivo no válido')

        self.load_medios(data['Medios'])
        self.load_personas(data['Personas'])
        self.load_programas(data['Programa  Sección'])

