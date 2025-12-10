from django.contrib import admin
from .models import NotaClinica # Importa tu modelo

# Opcional: Una clase sencilla para visualizarlo bien
class NotaClinicaAdmin(admin.ModelAdmin):
    list_display = ('cita', 'kinesiologo', 'paciente', 'fecha_creacion')
    list_filter = ('kinesiologo', 'paciente')
    search_fields = ('cita__pk', 'paciente__perfil__nombre')

# Registra el modelo
admin.site.register(NotaClinica, NotaClinicaAdmin)