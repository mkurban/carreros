from django import forms
from django.forms.models import modelform_factory
from django.forms import modelformset_factory, BaseModelFormSet
from material import Layout, Row
from .models import Fiscal
from elecciones.models import Mesa, VotoMesaReportado, Eleccion
from localflavor.ar.forms import ARDNIField


OPCION_CANTIDAD_DE_SOBRES = 22
OPCION_HAN_VOTADO = 21
OPCION_DIFERENCIA = 23
OPCION_TOTAL_VOTOS = 20


def opciones_actuales():
    try:
        return Eleccion.opciones_actuales.count()
    except:
        return 0


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


class FiscalFormSimple(FiscalForm):

    class Meta:
        model = Fiscal
        fields = [
            'nombres', 'apellido',
            'dni',
        ]



class VotoMesaModelForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['opcion'].label = ''
        self.fields['votos'].label = ''
        # self.fields['opcion'].widget.attrs['disabled'] = 'disabled'

    # layout = Layout(Row('opcion', 'votos'))

    class Meta:
        model = VotoMesaReportado
        fields = ('opcion', 'votos')


class BaseVotoMesaReportadoFormSet(BaseModelFormSet):
    def clean(self):
        super().clean()
        suma = 0
        for form in self.forms:
            opcion = form.cleaned_data['opcion']
            if opcion.id == OPCION_CANTIDAD_DE_SOBRES:
                cantidad_sobres = form.cleaned_data['votos']
            elif opcion.id == OPCION_HAN_VOTADO:
                han_votado = form.cleaned_data['votos']
            elif opcion.id == OPCION_DIFERENCIA:
                diferencia = form.cleaned_data['votos']
                form_opcion_dif = form
            elif opcion.id == OPCION_TOTAL_VOTOS:
                form_opcion_total = form
                total_en_acta = form.cleaned_data['votos']
            else:
                suma += form.cleaned_data['votos']

        if abs(diferencia) != abs(cantidad_sobres - han_votado):
            form_opcion_dif.add_error('votos', 'Diferencia no válida')

        if suma != total_en_acta:
            form_opcion_total.add_error(
                'votos', 'La sumatoria no se corresponde con el total'
            )
        if cantidad_sobres != total_en_acta:
            form_opcion_total.add_error(
                'votos', 'El total no corresponde a la cantidad de sobres'
            )


VotoMesaReportadoFormset = modelformset_factory(
    VotoMesaReportado, form=VotoMesaModelForm,
    formset=BaseVotoMesaReportadoFormSet,
    min_num=opciones_actuales(), extra=0, can_delete=False
)


EstadoMesaModelForm = modelform_factory(
    Mesa,
    fields=['estado'],
    widgets={"estado": forms.HiddenInput}
)