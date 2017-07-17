from django.contrib import admin
from .models import Persona, Medio, Programa, Aparicion, DatoDeContacto, Rol
from attachments.admin import AttachmentInlines


class AparicionAdmin(admin.ModelAdmin):
    inlines = (AttachmentInlines,)


admin.site.register(Aparicion, AparicionAdmin)
for model in (Persona, Medio, Programa, DatoDeContacto, Rol):
    admin.site.register(model)

# Register your models here.
