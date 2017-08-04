from django import forms
from django.forms.models import modelform_factory
from django.forms import inlineformset_factory, BaseInlineFormSet
from material import Layout, Row
from .models import Fiscal
from elecciones.models import Mesa, VotoMesaReportado, Eleccion
from localflavor.ar.forms import ARDNIField


OPCION_CANTIDAD_DE_SOBRES = 22
OPCION_HAN_VOTADO = 21
OPCION_DIFERENCIA = 23
OPCION_TOTAL_VOTOS = 20

OPCIONES = lambda: Eleccion.opciones_actuales()


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


class VotoMesaModelForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['opcion'].label = ''
        # self.fields['opcion'].required = False
        self.fields['votos'].label = ''
        self.fields['opcion'].widget.attrs['disabled'] = 'disabled'

    opcion_ = forms.ModelChoiceField(queryset=OPCIONES(), widget=forms.HiddenInput)

    layout = Layout(Row('opcion', 'votos'))

    class Meta:
        model = VotoMesaReportado
        fields = ('opcion', 'votos')


class VotoMesaInlineFormSet(BaseInlineFormSet):
    def clean(self):
        result = super().clean()
        import ipdb; ipdb.set_trace()
        suma = 0

        for form in self.forms:
            opcion = form.cleaned_data['opcion_']
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
                'votos', 'La suma no coincide con el total reportado'
            )


        if total_en_acta != suma:
            form_opcion_total.add_error(
                'votos', 'La suma de votos no coincide con el total reportado'
            )



VotoMesaReportadoFormset = inlineformset_factory(
    Mesa, VotoMesaReportado, form=VotoMesaModelForm,
    formset=VotoMesaInlineFormSet,
    min_num=OPCIONES().count(), extra=0, can_delete=False
)


EstadoMesaModelForm = modelform_factory(
    Mesa,
    fields=['estado'],
    widgets={"estado": forms.HiddenInput}
)



