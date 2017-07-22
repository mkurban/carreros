# -*- coding: utf-8 -*-
from django.views.generic.base import ContextMixin
from django.forms.models import ModelForm
from material.frontend.views import ModelViewSet, UpdateModelView, CreateModelView

from .forms import ContactoInlineFormset, ProgramaModelForm
from . import models


class ConContactosMixin(ContextMixin):

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        if self.request.POST:
            formset = ContactoInlineFormset(self.request.POST, instance=self.object)
        else:
            formset = ContactoInlineFormset(instance=self.object)
        context['formsets'] = {'Datos de contacto': formset}
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        valid = all(formset.is_valid() for formset in context['formsets'].values())
        if valid:
            self.object = form.save()
            for formset in context['formsets'].values():
                formset.instance = self.object
                formset.save()
            # ok, redirect
            return super().form_valid(form)

        # invalid formset
        return self.render_to_response(self.get_context_data(form=form))


class ConContactosUpdateModelView(ConContactosMixin, UpdateModelView):
    pass


class ConContactosCreateModelView(ConContactosMixin, CreateModelView):
    pass


class ConContactosModelViewSet(ModelViewSet):
    update_view_class = ConContactosUpdateModelView
    create_view_class = ConContactosCreateModelView


class MedioViewSet(ConContactosModelViewSet):
    model = models.Medio
    list_display = ('nombre', 'tipo', 'localidad')


class ProgramaViewSet(ConContactosModelViewSet):

    model = models.Programa
    form_class = ProgramaModelForm
    list_display = ('nombre', 'medio', 'localidad')
    list_display_links = list_display[:2]


class PersonaViewSet(ConContactosModelViewSet):
    model = models.Persona
    list_display = ('apellido', 'nombres', 'relacion', 'get_localidad')
    list_display_links = list_display[:2]


class DatoDeContactoViewSet(ModelViewSet):
    model = models.DatoDeContacto