from django.http import Http404
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView
from django.forms.models import modelform_factory
from django.contrib import messages
from .models import Fiscal
from elecciones.models import Mesa
from django.forms import HiddenInput
from .forms import MisDatosForm
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
    form_class = modelform_factory(Mesa, fields=['estado'], widgets={"estado": HiddenInput})

    def get_initial(self):
        initial = super().get_initial()
        initial['estado'] = self.object.proximo_estado
        return initial

    def get_success_url(self):
        messages.success(self.request, "El estado de la mesa cambió satisfactoriamente")
        return reverse('detalle-mesa', args=(self.object.numero,))



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


