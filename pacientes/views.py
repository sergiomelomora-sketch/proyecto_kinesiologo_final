# pacientes/views.py
from django.shortcuts import render, get_object_or_404
from usuarios.models import Paciente 

def listado_pacientes(request):
    """Muestra el listado de todos los pacientes."""
    pacientes = Paciente.objects.all().order_by('perfil__user__last_name')
    context = {'pacientes': pacientes}
    
    
    return render(request, 'pacientes_list.html', context) 

def detalle_paciente(request, pk):
    """Muestra el detalle/perfil de un paciente."""
    paciente = get_object_or_404(Paciente, pk=pk)
    
    context = {
        'paciente': paciente,
    }
    
    
    return render(request, 'pacientes_perfil.html', context)