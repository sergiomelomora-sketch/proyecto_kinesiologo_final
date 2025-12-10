# usuarios/admin.py

from django.contrib import admin

from .models import Perfil, Kinesiologo 


admin.site.register(Perfil)
admin.site.register(Kinesiologo)