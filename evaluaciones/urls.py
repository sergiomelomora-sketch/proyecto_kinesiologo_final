# evaluaciones/urls.py

from django.urls import path
from . import views

app_name = 'evaluaciones'

urlpatterns = [
    # 1. Rutas de LISTADO (Mantienen el enfoque en el Paciente)
    path('', views.listado_evaluaciones, name='listado_evaluaciones_general'),
    path('paciente/<int:paciente_pk>/', views.listado_evaluaciones, name='listado_evaluaciones_paciente'),
    
    # 2. Rutas de NOTA CLÍNICA (Enfoque en la Cita para crear/ver)
    # Nueva ruta para crear o editar la nota de una cita específica
    path('cita/<int:cita_pk>/nota/', views.crear_o_editar_nota_clinica, name='crear_o_editar_nota_clinica'),
    # Nueva ruta para ver la nota de una cita específica
    path('cita/<int:cita_pk>/ver/', views.ver_nota_clinica, name='ver_nota_clinica'),
    
    # NOTA: La ruta 'nueva_evaluacion' queda obsoleta, ya que la creación se hace a través de 'cita/<int:cita_pk>/nota/'.
]