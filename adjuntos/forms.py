from django import forms
from elecciones.models import Mesa


class AsignarMesaForm(forms.Form):
    mesa = forms.IntegerField(label='Nº Mesa', help_text='A que número pertenece esta acta')

    def clean_mesa(self):
        numero = self.cleaned_data['mesa']
        try:
            mesa = Mesa.objects.get(
                numero=numero, eleccion__id=3, attachment__isnull=True, foto_del_acta=''
            )
        except Mesa.DoesNotExist:
            raise forms.ValidationError('Esta mesa ya tiene acta adjunta')
        return mesa

