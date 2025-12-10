# pacientes/urls.py
from django.urls import path
from . import views

app_name = 'pacientes'

urlpatterns = [
    
    path('', views.listado_pacientes, name='listado_pacientes'),
    
    
    path('<int:pk>/perfil/', views.detalle_paciente, name='detalle_paciente'), 
]