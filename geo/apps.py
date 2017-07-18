from django.apps import AppConfig
from material.frontend.apps import ModuleMixin


class GeoConfig(ModuleMixin, AppConfig):
    name = 'geo'
    icon = '<i class="material-icons">settings_applications</i>'