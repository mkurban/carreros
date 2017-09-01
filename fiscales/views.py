from django.http import Http404, HttpResponseForbidden, HttpResponse
from django.conf import settings
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView, CreateView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.utils import timezone
from annoying.functions import get_object_or_None
from prensa.forms import MinimoContactoInlineFormset
from .models import Fiscal, AsignacionFiscalGeneral, AsignacionFiscalDeMesa
from elecciones.models import Mesa, Eleccion, VotoMesaReportado
from formtools.wizard.views import SessionWizardView
from django.template.loader import render_to_string
from html2text import html2text
from django.core.mail import send_mail

from .forms import (
    MisDatosForm,
    FiscalFormSimple,
    VotoMesaReportadoFormset,
    ActaMesaModelForm,
    QuieroSerFiscal1,
    QuieroSerFiscal2
)
from prensa.views import ConContactosMixin



def choice_home(request):
    """
    redirige a una página en funcion del tipo de usuario
    """

    user = request.user
    if not user.is_authenticated:
        return redirect('login')
    try:
        user.fiscal
        return redirect('donde-fiscalizo')
    except Fiscal.DoesNotExist:
        if user.groups.filter(name='prensa').exists():
            return redirect('/prensa/')
        elif user.is_staff:
            return redirect('/admin/')


class BaseFiscal(LoginRequiredMixin, DetailView):
    model = Fiscal

    def get_object(self, *args, **kwargs):
        try:
            return self.request.user.fiscal
        except Fiscal.DoesNotExist:
            raise Http404('no está registrado como fiscal')


class QuieroSerFiscal(SessionWizardView):
    form_list = [QuieroSerFiscal1, QuieroSerFiscal2]

    def get_form_initial(self, step):
        if step == '1':
            dni = self.get_cleaned_data_for_step('0')['dni']
            fiscal = get_object_or_None(Fiscal, dni=dni)
            if fiscal:
                if self.steps.current == '0':
                    messages.info(self.request, 'Ya estás en el sistema. Por favor, confirmá tus datos.')
                return {
                    'nombre': fiscal.nombres,
                    'apellido': fiscal.apellido,
                    'telefono': fiscal.telefonos[0] if fiscal.telefonos else '',
                    'email': fiscal.emails[0] if fiscal.emails else '',
                    'email2': fiscal.emails[0] if fiscal.emails else '',
                    'escuela': fiscal.escuelas[0] if fiscal.escuelas else None
                }
        return self.initial_dict.get(step, {})

    def done(self, form_list, **kwargs):
        data = self.get_all_cleaned_data()
        dni = data['dni']
        fiscal = get_object_or_None(Fiscal, dni=dni)
        if fiscal:
            fiscal.estado = 'AUTOCONFIRMADO'
        else:
            fiscal = Fiscal(estado='PRE-INSCRIPTO', tipo='de_mesa')
        email = data['email']
        fiscal.nombres = data['nombre']
        fiscal.apellido = data['apellido']
        fiscal.escuela_donde_vota = data['escuela']
        fiscal.save()
        fiscal.agregar_dato_de_contacto('teléfono', data['telefono'])
        fiscal.agregar_dato_de_contacto('email', email)

        body_html = render_to_string('fiscales/email.html', {'nombre': fiscal.nombres})
        body_text = html2text(body_html)

        # send_mail(
        #     'Recibimos tu inscripción como fiscal',
        #     body_text,
        #     'info@cordobaciudadana.org',
        #     [email],
        #     fail_silently=False,
        #     html_message=body_html
        # )

        return render(self.request, 'formtools/wizard/wizard_done.html', {
            'fiscal': fiscal,
        })


def email(request):
    html = render_to_string('fiscales/email.html', {'nombre': 'Pedro'})
    return HttpResponse(html2text(html), content_type='plain/text')
    # return render(request, 'fiscales/email.html', {})


class MisDatos(BaseFiscal):
    template_name = "fiscales/mis-datos.html"


class MisDatosUpdate(ConContactosMixin, UpdateView, BaseFiscal):
    """muestras los contactos para un fiscal"""
    form_class = MisDatosForm
    template_name = "fiscales/mis-datos-update.html"

    def get_success_url(self):
        return reverse('mis-datos')


class MisContactos(BaseFiscal):
    template_name = "fiscales/mis-contactos.html"


@login_required
def asignacion_estado(request, tipo, pk):
    fiscal = get_object_or_404(Fiscal, user=request.user)

    if tipo == 'de_mesa':
        asignacion = get_object_or_404(AsignacionFiscalDeMesa, id=pk)
        if asignacion.mesa not in fiscal.mesas_asignadas:
            raise Http404()
    else:
        asignacion = get_object_or_404(AsignacionFiscalGeneral, id=pk, fiscal=fiscal)

    comida_post = 'comida' in request.POST
    comida_get = 'comida' in request.GET     # fiscal general
    if comida_post or comida_get:
        asignacion.comida = 'recibida'
        asignacion.save(update_fields=['comida'])
        messages.info(request, '¡Buen provecho!' if comida_post else '¡Gracias!')

    elif not asignacion.ingreso:
        # llega por primera vez
        asignacion.ingreso = timezone.now()
        asignacion.egreso = None
        messages.info(request, 'Tu presencia se registró ¡Gracias!')
    elif asignacion.ingreso and not asignacion.egreso:
        # se retiró
        asignacion.egreso = timezone.now()
        messages.info(request, 'Anotamos el retiro, ¡Gracias!')
    elif asignacion.ingreso and asignacion.egreso:
        asignacion.ingreso = timezone.now()
        asignacion.egreso = None
        messages.info(request, 'Vamos a volver!')
    asignacion.save()
    mesa = request.GET.get('mesa')
    if mesa:
        return redirect(asignacion.mesa.get_absolute_url())
    return redirect('donde-fiscalizo')


class MiMesaMixin:
    def dispatch(self, *args, **kwargs):
        d = super().dispatch(*args, **kwargs)
        self.fiscal = get_object_or_404(Fiscal, tipo='general', user=self.request.user)
        self.mesa = self.get_mesa()
        if self.mesa not in self.fiscal.mesas_asignadas:
            return HttpResponseForbidden()
        return d

    def get_mesa(self):
        return get_object_or_404(Mesa, eleccion__id=self.kwargs['eleccion_id'], numero=self.kwargs['mesa_numero'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mesa'] = self.get_mesa()
        return context

    def verificar_fiscal_existente(self, fiscal):
        return fiscal


class MesaActa(BaseFiscal, UpdateView):
    template_name = "fiscales/cargar-foto.html"
    slug_field = 'numero'
    slug_url_kwarg = 'mesa_numero'
    model = Mesa
    form_class = ActaMesaModelForm

    def get_object(self):
        return get_object_or_404(Mesa, eleccion__id=self.kwargs['eleccion_id'],
                                 numero=self.kwargs['mesa_numero'], estado='ESCRUTADA')

    def form_valid(self, form):
        super().form_valid(form)
        messages.success(self.request, 'Foto subida correctamente ¡Gracias!')
        return redirect(self.object.get_absolute_url())


class BaseFiscalSimple(LoginRequiredMixin, MiMesaMixin, ConContactosMixin):
    """muestras los contactos para un fiscal"""
    form_class = FiscalFormSimple
    inline_formset_class = MinimoContactoInlineFormset
    model = Fiscal
    template_name = "fiscales/cargar-fiscal.html"

    def dispatch(self, *args, **kwargs):
        d = super().dispatch(*args, **kwargs)
        if not self.mesa.asignacion_actual:
            messages.error(self.request, 'No se registra fiscal en esta mesa ')
            return redirect(self.mesa.get_absolute_url())
        return d

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mesa'] = self.get_mesa()
        return context

    def form_valid(self, form):
        fiscal = form.save(commit=False)
        fiscal.tipo = 'de_mesa'
        fiscal = self.verificar_fiscal_existente(fiscal)
        fiscal.save()
        mesa = self.get_mesa()
        asignacion = mesa.asignacion_actual
        asignacion.fiscal = fiscal
        asignacion.save()
        messages.success(self.request, 'Fiscal cargado correctamente')
        return redirect(mesa.get_absolute_url())


class FiscalSimpleCreateView(BaseFiscalSimple, CreateView):

    def dispatch(self, *args, **kwargs):
        d = super().dispatch(*args, **kwargs)
        if not self.mesa.asignacion_actual:
            messages.error(self.request, 'No se registra fiscal en esta mesa ')
            return redirect(self.mesa.get_absolute_url())
        return d

    def verificar_fiscal_existente(self, fiscal):
        existente = get_object_or_None(Fiscal,
                dni=fiscal.dni,
                tipo_dni=fiscal.tipo_dni
            )
        if existente:
            fiscal = existente
            messages.info(self.request, 'Ya teniamos datos de esta persona')
        return fiscal


class FiscalSimpleUpdateView(BaseFiscalSimple, UpdateView):

    def get_object(self):
        mesa = self.get_mesa()
        fiscal = mesa.asignacion_actual.fiscal
        if fiscal:
            return fiscal
        raise Http404


@login_required
def eliminar_asignacion(request, eleccion_id, mesa_numero):
    fiscal = get_object_or_404(Fiscal, tipo='general', user=request.user)
    mesa = get_object_or_404(Mesa, eleccion__id=eleccion_id, numero=mesa_numero)
    if mesa not in fiscal.mesas_asignadas:
        return HttpResponseForbidden()
    mesa.asignacion_actual.delete()
    messages.success(request, 'La asignación se eliminó')
    return redirect(mesa.get_absolute_url())



@login_required
def tengo_fiscal(request, eleccion_id, mesa_numero):
    fiscal = get_object_or_404(Fiscal, tipo='general', user=request.user)
    mesa = get_object_or_404(Mesa, eleccion__id=eleccion_id, numero=mesa_numero)
    if mesa not in fiscal.mesas_asignadas:
        return HttpResponseForbidden()

    _, created = AsignacionFiscalDeMesa.objects.get_or_create(
        mesa=mesa,
        defaults={'ingreso': timezone.now(), 'egreso': None}
    )
    if created:
        messages.info(request, 'Registramos que la mesa tiene fiscal')
    else:
        messages.warning(request, 'Esta mesa ya tiene un fiscal registrado')
    return redirect(mesa.get_absolute_url())



@login_required
def mesa_cambiar_estado(request, eleccion_id, mesa_numero, estado):
    fiscal = get_object_or_404(Fiscal, user=request.user)
    mesa = get_object_or_404(Mesa, eleccion__id=eleccion_id, numero=mesa_numero)
    if mesa not in fiscal.mesas_asignadas:
        return HttpResponseForbidden()
    mesa.estado = estado
    mesa.save()
    success_msg = "El estado de la mesa se cambió correctamente"
    messages.success(request, success_msg)
    return redirect(mesa.get_absolute_url())


class DondeFiscalizo(BaseFiscal):
    template_name = "fiscales/donde-fiscalizo.html"


class MesaDetalle(LoginRequiredMixin, MiMesaMixin, DetailView):
    template_name = "fiscales/mesa-detalle.html"
    slug_field = 'numero'
    slug_url_kwarg = 'mesa_numero'
    model = Mesa



@login_required
def cargar_resultados(request, eleccion_id, mesa_numero):
    def fix_opciones(formset):
        # hack para dejar sólo la opcion correspondiente a cada fila
        # se podria hacer "disabled" pero ese caso quita el valor del
        # cleaned_data y luego lo exige por ser requerido.
        for opcion, form in zip(Eleccion.opciones_actuales(), formset):
            form.fields['opcion'].choices = [(opcion.id, str(opcion))]

            # si la opcion es obligatoria, se llenan estos campos
            if opcion.obligatorio:
                form.fields['votos'].required = True

    mesa = get_object_or_404(Mesa, eleccion__id=eleccion_id, numero=mesa_numero)
    try:
        fiscal = request.user.fiscal
    except Fiscal.DoesNotExist:
        raise Http404()

    if mesa not in fiscal.mesas_asignadas:
        return HttpResponseForbidden()

    data = request.POST if request.method == 'POST' else None
    qs = VotoMesaReportado.objects.filter(mesa=mesa, fiscal=fiscal)
    initial = [{'opcion': o} for o in Eleccion.opciones_actuales()]
    formset = VotoMesaReportadoFormset(data, queryset=qs, initial=initial)

    fix_opciones(formset)

    is_valid = False
    if qs:
        formset.convert_warnings = True  # monkepatch

    if request.method == 'POST' or qs:
        is_valid = formset.is_valid()

    # eleccion = Eleccion.objects.last()
    if is_valid:
        for form in formset:
            vmr = form.save(commit=False)
            vmr.mesa = mesa
            vmr.fiscal = fiscal
            # vmr.eleccion = eleccion
            vmr.save()

        if formset.warnings:
            messages.warning(request, 'Guardado con inconsistencias')
        else:
            messages.success(request, 'Guardado correctamente')

        return redirect(mesa)

    return render(request, "fiscales/carga.html",
        {'formset': formset, 'object': mesa})


class CambiarPassword(PasswordChangeView):
    template_name = "fiscales/cambiar-contraseña.html"
    success_url = reverse_lazy('mis-datos')

    def form_valid(self, form):
        messages.success(self.request, 'Tu contraseña se cambió correctamente')
        return super().form_valid(form)


