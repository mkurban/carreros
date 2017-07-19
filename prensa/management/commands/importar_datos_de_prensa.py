import re
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from pyexcel_io.exceptions import NoSupportingPluginFound
from pyexcel_xlsx import get_data
from prensa.models import Persona, Medio, Programa
from prensa.forms import DatoDeContactoModelForm
from geo.models import Localidad


LUIS = User.objects.get(username='luis')


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
        emails = re.findall(r'[\w\.-]+@[\w\.-]+', raw)
        telefonos = re.findall(r'(?:^|\s)(0?3\d+\s?\d+|4\d+|5\d+)', raw)
        urls = re.findall(r'https?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', raw)
        return {'email': emails, 'teléfono': telefonos, 'web': urls}

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

                for tipo, valores in datos_de_contacto.items():
                    for valor in valores:
                        d = DatoDeContactoModelForm({
                            'tipo': tipo,
                            'valor': valor,
                            'content_type': ct.id,
                            'object_id': medio.id
                        })
                        if d.is_valid():
                            dato = d.save()
                            self.success(f'Importado {dato} para {medio}')
                        else:
                            self.warning(f'Ignorado {d.errors}')



    def handle(self, *args, **options):

        path = options['xlsx']
        try:
            data = get_data(path)
            assert list(data.keys())[:3] == Command.HOJAS
        except (AssertionError, NoSupportingPluginFound):
            raise CommandError('Archivo no válido')


        self.load_medios(data['Medios'])

