from django import forms
from .models import Attachment
from elecciones.models import Mesa


class AsignarMesaForm(forms.ModelForm):
    mesa = forms.IntegerField(label='Nº Mesa',
        required=False,
        help_text='A que número pertenece esta acta'
    )

    class Meta:
        model = Attachment
        fields = ['mesa', 'problema']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mesa'].widget.attrs['tabindex'] = 1
        self.fields['mesa'].widget.attrs['autofocus'] = True
        self.fields['problema'].widget.attrs['tabindex'] = 99

    def clean_mesa(self):
        numero = self.cleaned_data['mesa']
        if not numero:
            return numero
        try:
            mesa = Mesa.objects.get(
                numero=numero, eleccion__id=3, attachment__isnull=True, foto_del_acta=''
            )
        except Mesa.DoesNotExist:
            raise forms.ValidationError('Esta mesa ya tiene acta adjunta')
        return mesa

    def clean(self):
        cleaned_data = super().clean()
        problema = cleaned_data.get('problema')
        mesa = cleaned_data.get('mesa')
        if not mesa and not problema:
            self.add_error(
                'mesa', 'Indicá la mesa o reportá un problema'
            )

        elif problema and mesa:
            cleaned_data['mesa'] = None
            self.add_error(
                'problema', 'Dejá el número en blanco si hay un problema'
            )
            return cleaned_data