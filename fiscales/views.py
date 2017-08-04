from django.http import Http404
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView
from django.contrib import messages
from django.http import HttpResponseForbidden

from .models import Fiscal
from elecciones.models import Mesa, Eleccion, VotoMesaReportado

from .forms import MisDatosForm, EstadoMesaModelForm, VotoMesaReportadoFormset
from prensa.views import ConContactosMixin
from django.contrib.auth.views import PasswordChangeView


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


class MisDatos(BaseFiscal):
    template_name = "fiscales/mis-datos.html"


class MisContactos(BaseFiscal):
    template_name = "fiscales/mis-contactos.html"


class DondeFiscalizo(BaseFiscal):
    template_name = "fiscales/donde-fiscalizo.html"


class MesaDetalle(LoginRequiredMixin, UpdateView):
    template_name = "fiscales/mesa-detalle.html"
    slug_field = 'numero'
    slug_url_kwarg = 'mesa_numero'
    model = Mesa
    form_class = EstadoMesaModelForm
    success_msg = "El estado de la mesa se cambió correctamente"

    def get_initial(self):
        initial = super().get_initial()
        initial['estado'] = self.object.proximo_estado
        return initial

    def get_success_url(self):
        messages.success(self.request, self.success_msg)
        return reverse('detalle-mesa', args=(self.object.numero,))


def cargar_mesa(request, mesa_numero):
    mesa = get_object_or_404(Mesa, numero=mesa_numero)
    fiscal = request.user.fiscal
    if mesa not in fiscal.mesas_asignadas():
        raise HttpResponseForbidden()

    data = request.POST if request.method == 'POST' else None
    qs = VotoMesaReportado.objects.filter(mesa=mesa, fiscal=fiscal)
    if qs.exists():
        formset = VotoMesaReportadoFormset(data, queryset=qs)
    else:
        initial = [{'opcion': o, 'opcion_': o} for o in Eleccion.opciones_actuales()]
        formset = VotoMesaReportadoFormset(data, initial=initial)

    if formset.is_valid():
        for form in formset:
            vmr = form.save(commit=False)
            vmr.mesa = mesa
            vmr.fiscal = fiscal
            vmr.eleccion = Eleccion.objects.last()
            vmr.save()
        messages.success(request, 'Los resultados se cargaron correctamente')
        return redirect('detalle-mesa', args=(mesa.numero,))

    return render(request, "fiscales/carga.html",
        {'formset': formset, 'object': mesa})




class MisDatosUpdate(ConContactosMixin, UpdateView, BaseFiscal):
    """muestras los contactos para un fiscal"""
    form_class = MisDatosForm
    template_name = "fiscales/mis-datos-update.html"

    def get_success_url(self):
        return reverse('mis-datos')


class CambiarPassword(PasswordChangeView):
    template_name = "fiscales/cambiar-contraseña.html"
    success_url = reverse_lazy('mis-datos')

    def form_valid(self, form):
        messages.success(self.request, 'Tu contraseña se cambió correctamente')
        return super().form_valid(form)


