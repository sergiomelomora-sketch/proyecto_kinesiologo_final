
# citas/admin.py

from django.contrib import admin
from .models import Cita # Asegúrate de importar Cita

@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha_hora_inicio', 'paciente', 'kinesiologo', 'estado')
    list_filter = ('estado', 'kinesiologo')
    search_fields = ('paciente__perfil__nombre', 'kinesiologo__perfil__nombre')
    date_hierarchy = 'fecha_hora_inicio'