# pacientes/admin.py

from django.contrib import admin
 
from usuarios.models import Paciente 


admin.site.register(Paciente)
