# usuarios/urls.py


from django.urls import path
from . import views
from .views import RegistroPacienteView 

app_name = 'usuarios'

urlpatterns = [
    
    path('login/', views.autenticar_paciente, name='autenticar_paciente'),

    path('kine/login/', views.autenticar_kinesiologo, name='autenticar_kinesiologo'),
    
    
    path('registro/', RegistroPacienteView.as_view(), name='registro_paciente'),

    
    path('logout/', views.logout_view, name='logout_view'),

    
    path('inicio/', views.inicio_usuarios, name='inicio'),
]