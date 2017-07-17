from django.apps import AppConfig
from material.frontend.apps import ModuleMixin


class PrensaConfig(ModuleMixin, AppConfig):
    name = 'prensa'
    icon = '<i class="material-icons">settings_applications</i>'
