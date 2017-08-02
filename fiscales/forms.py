from django import forms
from .models import Fiscal
from localflavor.ar.forms import ARDNIField


class FiscalForm(forms.ModelForm):
    dni = ARDNIField()

    class Meta:
        model = Fiscal
        exclude = []
