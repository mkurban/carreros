from django import forms
from .models import Fiscal
from localflavor.ar.forms import ARDNIField


class FiscalForm(forms.ModelForm):
    dni = ARDNIField()

    class Meta:
        model = Fiscal
        exclude = []


class MisDatosForm(FiscalForm):
    class Meta:
        model = Fiscal
        fields = [
            'nombres', 'apellido',
            'direccion', 'localidad',
            'barrio',
            'tipo_dni', 'dni',
            'organizacion'
        ]