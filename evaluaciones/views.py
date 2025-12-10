# evaluaciones/views.py (CÓDIGO MODIFICADO SOLO PARA DEPURACIÓN DE GUARDADO)

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
# from django.db import transaction, DatabaseError # Ya no es necesario DatabaseError, ni transaction

# Importaciones CLAVE
from citas.models import Cita, CITA_FINALIZADA
from usuarios.models import Kinesiologo, Paciente, KINESIOLOGO
from .models import NotaClinica 
from .forms import NotaClinicaForm 

# ----------------------------------------------------------------------
# VISTAS DE LISTADO (Sin cambios)
# ----------------------------------------------------------------------

@login_required
def listado_evaluaciones(request, paciente_pk=None):
    """Lista las Notas Clínicas, opcionalmente filtradas por paciente."""
    
    # Restricción de seguridad
    if request.user.perfil.rol != KINESIOLOGO and not request.user.is_superuser:
        messages.error(request, "Acceso no autorizado.")
        return redirect('index')

    if paciente_pk:
        paciente = get_object_or_404(Paciente, pk=paciente_pk)
        notas = NotaClinica.objects.filter(paciente=paciente).order_by('-fecha_creacion')
    else:
        try:
            kine = Kinesiologo.objects.get(perfil__user=request.user)
            notas = NotaClinica.objects.filter(kinesiologo=kine).order_by('-fecha_creacion')
        except Kinesiologo.DoesNotExist:
            notas = NotaClinica.objects.none()
            messages.warning(request, "No se encontraron notas clínicas asociadas a tu perfil.")
            
    context = {'notas': notas, 'paciente': paciente if paciente_pk else None}
    
    # RUTA DE PLANTILLA CORREGIDA: 'evaluaciones_list.html'
    return render(request, 'evaluaciones_list.html', context)

# ----------------------------------------------------------------------
# VISTAS DE NOTA CLÍNICA (SIN TRANSACTION.ATOMIC)
# ----------------------------------------------------------------------

@login_required
# @transaction.atomic <--- ¡COMENTADO O ELIMINADO PARA FORZAR EL ERROR VISIBLE!
def crear_o_editar_nota_clinica(request, cita_pk):
    """
    Permite al Kinesiólogo crear o editar la nota clínica asociada a una Cita.
    """
    cita = get_object_or_404(Cita, pk=cita_pk)
    
    # Restricción de seguridad
    # Usando cita.kinesiologo.perfil.user para asegurar que el Kine logueado es el asignado a la cita
    if request.user.perfil.rol != KINESIOLOGO or cita.kinesiologo.perfil.user != request.user:
        messages.error(request, "Acceso no autorizado.")
        return redirect('index')
    
    try:
        nota_existente = NotaClinica.objects.get(cita=cita)
    except NotaClinica.DoesNotExist:
        nota_existente = None
        
    if request.method == 'POST':
        form = NotaClinicaForm(request.POST, instance=nota_existente)
        
        if form.is_valid():
            # RESTAURADO EL CÓDIGO LIMPIO SIN TRY/EXCEPT DE BASE DE DATOS
            nota = form.save(commit=False)
            nota.cita = cita
            nota.kinesiologo = cita.kinesiologo 
            nota.paciente = cita.paciente 
            nota.save()
            
            # Cambiar estado de la Cita a FINALIZADA
            if cita.estado != CITA_FINALIZADA:
                cita.estado = CITA_FINALIZADA
                cita.save()
                
            messages.success(request, f"Nota clínica para la cita #{cita_pk} guardada y cita marcada como Finalizada.")
            # Redirección a dashboard de citas (SOLO SI FUE EXITOSO)
            return redirect(reverse('citas:kinesiologo_dashboard'))
            
        else:
            # Si form.is_valid() es False, establecemos el mensaje y el flujo continúa al render
            messages.error(request, "Error de validación. Revisa los campos obligatorios.")
    else:
        form = NotaClinicaForm(instance=nota_existente)
        
    context = {
        'form': form,
        'cita': cita,
        'paciente': cita.paciente,
        'es_edicion': nota_existente is not None
    }
    # RUTA DE PLANTILLA CORREGIDA: 'crear_o_editar_nota.html'
    return render(request, 'crear_o_editar_nota.html', context)


@login_required
def ver_nota_clinica(request, cita_pk):
    """
    Permite ver la nota clínica. Accesible por Kinesiólogo (su cita) o Paciente (su cita).
    """
    cita = get_object_or_404(Cita, pk=cita_pk)
    
    # Restricción de seguridad
    es_kine = request.user.perfil.rol == KINESIOLOGO and cita.kinesiologo.perfil.user == request.user
    es_paciente = cita.paciente.perfil.user == request.user
    
    if not (request.user.is_superuser or es_kine or es_paciente):
        messages.error(request, "Acceso denegado a esta nota clínica.")
        return redirect('index')

    try:
        nota = NotaClinica.objects.get(cita=cita)
    except NotaClinica.DoesNotExist:
        messages.warning(request, "La nota clínica para esta cita aún no ha sido registrada.")
        
        if es_kine:
            # REDIRECCIÓN CORRECTA: Usando el namespace 'evaluaciones:'
            return redirect(reverse('evaluaciones:crear_o_editar_nota_clinica', kwargs={'cita_pk': cita_pk}))
        
        return redirect(reverse('citas:agenda'))

    context = {
        'nota': nota,
        'cita': cita,
        'es_kine': es_kine
    }
    # RUTA DE PLANTILLA CORREGIDA: 'ver_nota.html'
    return render(request, 'ver_nota.html', context)