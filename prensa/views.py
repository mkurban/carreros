# -*- coding: utf-8 -*-
from material.frontend.views import ModelViewSet, UpdateModelView
from django.contrib.contenttypes.forms import generic_inlineformset_factory
from . import models



class ConContactos(UpdateModelView):

    def get_context_data(self, **kwargs):

        ContactoFormset = generic_inlineformset_factory(models.DatoDeContacto)      # noqa

        context = super().get_context_data(**kwargs)

        if self.request.POST:
            formset = ContactoFormset(self.request.POST, instance=self.object)
        else:
            formset = ContactoFormset(instance=self.object)
        context['formsets'] = {'Datos de contacto': formset}
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        valid = all(formset.is_valid() for formset in context['formsets'].values())
        if valid:
            for formset in context['formsets'].values():
                self.object = form.save()
                formset.instance = self.object
                formset.save()
        return self.render_to_response(self.get_context_data(form=form))


class MedioViewSet(ModelViewSet):
    model = models.Medio
    list_display = ('nombre', 'tipo', 'localidad')


class PersonaViewSet(ModelViewSet):
    model = models.Persona
    update_view_class = ConContactos
    list_display = ('apellido', 'nombres', 'relacion')



class DatoDeContactoViewSet(ModelViewSet):
    model = models.DatoDeContacto