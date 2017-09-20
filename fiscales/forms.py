from django import forms
from django.forms.models import modelform_factory
from django.forms import modelformset_factory, BaseModelFormSet
from django.utils.safestring import mark_safe
from material import Layout, Row, Fieldset
from .models import Fiscal
from elecciones.models import Mesa, VotoMesaReportado, Eleccion, LugarVotacion, Circuito, Seccion
from localflavor.ar.forms import ARDNIField
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _
from prensa.forms import validar_telefono
import phonenumbers


OPCION_CANTIDAD_DE_SOBRES = 22
OPCION_HAN_VOTADO = 21
OPCION_DIFERENCIA = 23
OPCION_TOTAL_VOTOS = 20

LINK = 'Si tenés dudas consultá el <a href="https://www.padron.gob.ar" target="_blank">padrón</a>'


class AuthenticationFormCustomError(AuthenticationForm):
    error_messages = {
        'invalid_login': "Por favor introduzca un nombre de usuario y una contraseña correctos. Prueba tu DNI o teléfono sin puntos, guiones ni espacios",
        'inactive': _("This account is inactive."),
    }



def opciones_actuales():
    try:
        return Eleccion.opciones_actuales().count()
    except:
        return 0


class FiscalForm(forms.ModelForm):

    dni = ARDNIField(required=False)

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



class FiscalForm(forms.ModelForm):

    dni = ARDNIField(required=False)

    class Meta:
        model = Fiscal
        exclude = []


class QuieroSerFiscal1(forms.Form):
    dni = ARDNIField(required=True, help_text='Ingresá tu Nº de documento')
    email = forms.EmailField(required=True)
    email2 = forms.EmailField(required=True, label="Confirmar email")

    layout = Layout('dni',
                    Row('email', 'email2'))


    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        email2 = cleaned_data.get('email2')
        if email and email2 and email != email2:
            self.add_error('email', 'Los emails no coinciden')
            self.add_error('email2', 'Los emails no coinciden')


class QuieroSerFiscal2(forms.ModelForm):
    nombre = forms.CharField()
    apellido = forms.CharField()
    telefono = forms.CharField(label='Teléfono', help_text='Preferentemente celular')
    movilidad = forms.BooleanField(
        label='¿Tenés Movilidad propia?', required=False,
        help_text='Marcá la casilla si tenés cómo movilizarte el día de la elección'
    )
    seccion = forms.ModelChoiceField(label='Sección electoral', queryset=Seccion.objects.all(),
        help_text=mark_safe(f'Sección/departamento donde votás y/o preferís fiscalizar. {LINK}')
    )

    layout = Layout(Row('nombre', 'apellido'),
                    'telefono',
                    Row('movilidad', 'disponibilidad'),
                    Fieldset('¿Dónde votás?',
                             'seccion'))
    class Meta:
        model = Fiscal
        fields = [
            'nombre', 'apellido', 'telefono', 'movilidad',
            'disponibilidad', 'seccion'
        ]


    def clean_telefono(self):
        valor = self.cleaned_data['telefono']
        try:
            valor = validar_telefono(valor)
        except (AttributeError, phonenumbers.NumberParseException):
            raise forms.ValidationError('No es un teléfono válido')
        return valor


class QuieroSerFiscal3(forms.Form):
    circuito = forms.ModelChoiceField(queryset=Circuito.objects.all(),
        help_text=mark_safe(f'Circuito/zona donde votás y/o preferís fiscalizar. {LINK}')
    )


class QuieroSerFiscal4(forms.Form):
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }

    escuela = forms.ModelChoiceField(queryset=LugarVotacion.objects.all(),
        help_text=mark_safe(f'Escuela donde votás y/o preferís fiscalizar. {LINK}')
    )
    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput,
        strip=False,
    )
    new_password2 = forms.CharField(
        label=_("New password confirmation"),
        strip=False,
        widget=forms.PasswordInput,
    )

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )
        return password2


class VotoMesaModelForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['opcion'].label = ''
        self.fields['votos'].label = ''
        self.fields['votos'].required = False

        # self.fields['opcion'].widget.attrs['disabled'] = 'disabled'

    # layout = Layout(Row('opcion', 'votos'))

    class Meta:
        model = VotoMesaReportado
        fields = ('opcion', 'votos')


class BaseVotoMesaReportadoFormSet(BaseModelFormSet):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.warnings = []


    def clean(self):
        super().clean()
        suma = 0
        for form in self.forms:
            opcion = form.cleaned_data['opcion']
            if opcion.id == OPCION_CANTIDAD_DE_SOBRES:
                cantidad_sobres = form.cleaned_data.get('votos') or 0
            elif opcion.id == OPCION_HAN_VOTADO:
                han_votado = form.cleaned_data.get('votos') or 0
            elif opcion.id == OPCION_DIFERENCIA:
                diferencia = form.cleaned_data.get('votos') or 0
                form_opcion_dif = form
            elif opcion.id == OPCION_TOTAL_VOTOS:
                form_opcion_total = form
                total_en_acta = form.cleaned_data.get('votos') or 0
            else:
                suma += form.cleaned_data.get('votos') or 0

        if abs(diferencia) != abs(cantidad_sobres - han_votado):

            # form_opcion_dif.add_error('votos', 'Diferencia no válida')
            self.warnings.append((form_opcion_dif, 'votos', 'Diferencia no valida'))

        if suma != total_en_acta:
            #form_opcion_total.add_error(
            #    'votos', 'La sumatoria no se corresponde con el total'
            #)
            self.warnings.append((form_opcion_total, 'votos', 'La sumatoria no se corresponde con el total'))

        if cantidad_sobres != total_en_acta:
            # form_opcion_total.add_error(
            #    'votos', 'El total no corresponde a la cantidad de sobres'
            # )
            self.warnings.append((form_opcion_total, 'votos', 'El total no corresponde a la cantidad de sobres'))


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


ActaMesaModelForm = modelform_factory(
    Mesa,
    fields=['foto_del_acta'],
)
