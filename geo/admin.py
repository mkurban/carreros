from django.contrib import admin

# Register your models here.
from .models import Localidad, Departamento

# Register your models here.
admin.site.register(Departamento)
admin.site.register(Localidad)

