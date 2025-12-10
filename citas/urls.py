# citas/urls.py

from django.urls import path
from . import views
from usuarios.views import index # Asumo que 'index' viene de usuarios.views

app_name = 'citas' 

urlpatterns = [
    
    # Vistas de Paciente / Generales
    path('agenda/', views.agenda, name='agenda'),
    path('detalle/<int:pk>/', views.detalle_cita, name='detalle_cita'),
    path('agendar/', views.NuevaCitaView.as_view(), name='agendar_cita'), 
    path('confirmacion/<int:cita_id>/', views.confirmacion_cita, name='cita_confirmada'),
    
    # CANCELACIÓN DEL PACIENTE (Usando la vista renombrada)
    path('cancelar/paciente/<int:pk>/', views.cancelar_cita_paciente, name='cancelar_cita_paciente'), 
    
    # RUTA OBSOLETA ELIMINADA: 
    # path('cancelar/<int:pk>/', views.cancelar_cita, name='cancelar_cita'),
    # Esto ya no existe en views.py y fue reemplazado por la línea anterior.
    
    # Vistas del Kinesiólogo
    path('kinesiologo/dashboard/', views.KinesiologoDashboardView.as_view(), name='kinesiologo_dashboard'),
    path('kinesiologo/bloqueos/', views.gestionar_bloqueos, name='gestionar_bloqueos'),
    
    # API
    path('api/horarios/', views.obtener_horarios_disponibles, name='api_horarios'),
    
    # Dashboard (Usando la vista index de usuarios)
    path('dashboard/', index, name='dashboard'),
]