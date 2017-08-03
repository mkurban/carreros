from django.http import Http404
from django.shortcuts import redirect
from django.views.generic.detail import DetailView
from .models import Fiscal


def choice_home(request):
    user = request.user
    if not user.is_authenticated:
        return redirect('login')
    try:
        user.fiscal
        return redirect('mis-datos')
    except Fiscal.DoesNotExist:
        if user.groups.filter(name='prensa').exists():
            return redirect('/prensa/')
        elif user.is_staff:
            return redirect('/admin/')



class MisContactos(DetailView):
    """muestras los contactos para un fiscal"""
    template_name = "fiscales/mis-contactos.html"
    model = Fiscal

    def get_object(self, *args, **kwargs):
        try:
            return self.request.user.fiscal
        except Fiscal.DoesNotExist:
            raise Http404('no está registrado como fiscal')


class MisDatos(MisContactos):
    """muestras los contactos para un fiscal"""
    template_name = "fiscales/mis-datos.html"
