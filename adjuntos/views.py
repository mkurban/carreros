from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.generic.edit import FormView
from django.db.models import Q
from elecciones.views import StaffOnlyMixing
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from datetime import timedelta
from .models import Attachment
from .forms import AsignarMesaForm


WAITING_FOR = 3   # 3 minutos


@staff_member_required
def elegir_adjunto(request):
    now = timezone.now()
    desde = now - timedelta(minutes=WAITING_FOR)

    # se eligen actas que nunca se intentaron cargar o que se asignaron a
    # hace más de 3 minutos
    attachments = Attachment.objects.filter(
        Q(taken__isnull=True) | Q(taken__lt=desde, mesa__isnull=True)
    ).order_by('?')
    if attachments.exists():
        a = attachments[0]
        # se marca el adjunto
        a.taken = now
        a.save(update_fields=['taken'])
        return redirect('asignar-mesa', attachment_id=a.id)

    return render(request, 'adjuntos/sin-actas.html')



class AsignarMesaAdjunto(StaffOnlyMixing, FormView):
    form_class = AsignarMesaForm
    template_name = "adjuntos/asignar-mesa.html"

    def dispatch(self, *args, **kwargs):
        self.attachment = get_object_or_404(Attachment, id=self.kwargs['attachment_id'])
        return super().dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('elegir-adjunto')

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context['attachment'] = self.attachment
        return context

    def form_valid(self, form):
        self.attachment.mesa = form.cleaned_data['mesa']
        self.attachment.save(update_fields=['mesa'])
        return super().form_valid(form)

