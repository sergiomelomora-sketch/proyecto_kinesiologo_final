from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.contrib import messages
from datetime import datetime, date
from django.db.models import Q 
from django.http import JsonResponse
from datetime import timedelta
from django.utils import timezone 
from django.contrib.auth.decorators import login_required
from django.db import transaction 
from django.core.exceptions import ObjectDoesNotExist 

# Importaciones de modelos y constantes necesarios
from usuarios.models import Paciente, Kinesiologo, KINESIOLOGO
from .forms import CitaForm, BloqueoHorarioForm
from .models import Cita, BloqueoHorario, CITA_PENDIENTE, CITA_CANCELADA, CITA_FINALIZADA, CITA_CONFIRMADA

# ----------------------------------------------------------------------
# Vistas del Paciente
# ----------------------------------------------------------------------

def agenda(request):
    """Muestra la lista de citas próximas del paciente."""
    if not request.user.is_authenticated:
        return redirect('usuarios:autenticar_paciente') 

    hoy = timezone.now()
    
    try:
        paciente = Paciente.objects.get(perfil__user=request.user)
        citas_proximas = Cita.objects.filter(
            paciente=paciente,
            fecha_hora_inicio__gte=hoy
        ).order_by('fecha_hora_inicio')
    except Paciente.DoesNotExist:
        messages.warning(request, "Tu perfil de Paciente no está configurado.")
        citas_proximas = Cita.objects.none() 

    context = {
        'citas': citas_proximas,
        'hoy': hoy,
    }
    return render(request, 'citas_agenda.html', context)


def detalle_cita(request, pk):
    """Muestra el detalle de una cita específica."""
    cita = get_object_or_404(Cita, pk=pk)
    
    # Restricción de seguridad
    if not request.user.is_superuser and cita.paciente.perfil.user != request.user:
          messages.error(request, "Acceso denegado: Esta no es su cita.")
          return redirect(reverse('citas:agenda'))
          
    return render(request, 'detalle.html', {'cita': cita})


@login_required
@transaction.atomic 
def cancelar_cita_paciente(request, pk):
    """
    Permite al Paciente logueado cancelar su propia cita.
    Esta función es accedida por POST desde detalle.html.
    """
    cita = get_object_or_404(Cita, pk=pk)
    
    # 1. Seguridad: Verificar propiedad del paciente
    if not request.user.is_superuser and cita.paciente.perfil.user != request.user:
        messages.error(request, "Acceso denegado: No puedes cancelar la cita de otro paciente.")
        return redirect(reverse('citas:agenda'))
        
    # 2. Lógica de cancelación
    if request.method == 'POST':
        try:
            # Solo permitir cancelar si la cita no está Finalizada o ya Cancelada
            if cita.estado == CITA_FINALIZADA or cita.estado == CITA_CANCELADA:
                messages.warning(request, "Esta cita ya está finalizada o ya había sido cancelada.")
                return redirect(reverse('citas:agenda')) 
                
            cita.estado = CITA_CANCELADA 
            cita.save()
            messages.success(request, f"Cita #{cita.pk} cancelada con éxito. Sentimos el inconveniente.")
            
        except Exception as e:
            messages.error(request, f"Error inesperado al intentar cancelar la cita: {e}")
            
        # Redirigir siempre a la agenda del paciente después del POST
        return redirect(reverse('citas:agenda')) 
    
    # Si alguien intenta acceder a esta URL con GET (solo debería ser POST)
    messages.warning(request, "Acción no permitida. La cancelación debe hacerse desde la vista de detalle.")
    return redirect(reverse('citas:agenda'))


def confirmacion_cita(request, cita_id):
    """Muestra los detalles de la cita agendada para la confirmación."""
    cita = get_object_or_404(Cita, pk=cita_id)
    
    if not request.user.is_superuser and cita.paciente.perfil.user != request.user:
          messages.error(request, "Acceso denegado a la confirmación.")
          return redirect(reverse('citas:agenda'))
          
    context = {
        'cita': cita
    }
    return render(request, 'confirmacion.html', context)


class NuevaCitaView(LoginRequiredMixin, View):
    """Maneja la presentación y el procesamiento del formulario de Cita."""
    
    template_name = 'nueva.html'
    
    def get(self, request):
        """Muestra el formulario vacío."""
        form = CitaForm()
        context = {
            'form': form,
            'titulo': 'Agendar Nueva Cita'
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Procesa el envío del formulario."""
        form = CitaForm(request.POST)
        
        if form.is_valid():
            try:
                
                paciente = Paciente.objects.get(perfil__user=request.user)
                
                cita = form.save(commit=False)
                cita.paciente = paciente
                
                # Asignar estado PENDIENTE por defecto
                cita.estado = CITA_PENDIENTE
                
                cita.save()
                
                return redirect(reverse('citas:cita_confirmada', kwargs={'cita_id': cita.pk}))
                
            except Paciente.DoesNotExist:
                messages.error(request, "Error de perfil. Solo los usuarios con perfil de Paciente pueden agendar citas.")
                
                return redirect(reverse('citas:agenda')) 
            except Exception as e:
                messages.error(request, f"Error inesperado al guardar la cita: {e}")
                
        
        context = {
            'form': form,
            'titulo': 'Agendar Nueva Cita (Error)'
        }
        return render(request, self.template_name, context)


HORA_INICIO_JORNADA = 9 
HORA_FIN_JORNADA = 18 
DURACION_CITA = 60 

def obtener_horarios_disponibles(request):
    """Retorna una lista JSON de las horas libres para un kinesiólogo y fecha dados."""
    kinesiologo_id = request.GET.get('kinesiologo_id')
    fecha_str = request.GET.get('fecha')

    if not kinesiologo_id or not fecha_str:
        return JsonResponse({'error': 'Faltan parámetros de Kinesiólogo o Fecha.'}, status=400)

    try:
        from datetime import datetime 
        
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        
        inicio_dia = timezone.make_aware(datetime.combine(fecha_obj, datetime.min.time().replace(hour=HORA_INICIO_JORNADA)))
        fin_dia = timezone.make_aware(datetime.combine(fecha_obj, datetime.min.time().replace(hour=HORA_FIN_JORNADA)))
        
        # Citas agendadas
        citas_agendadas = Cita.objects.filter(
            kinesiologo_id=kinesiologo_id,
            fecha_hora_inicio__date=fecha_obj
        ).values_list('fecha_hora_inicio', 'duracion_minutos')
        
        # Bloqueos de horario
        bloqueos = BloqueoHorario.objects.filter(
            kinesiologo_id=kinesiologo_id,
            fecha_hora_inicio__date=fecha_obj
        ).values_list('fecha_hora_inicio', 'fecha_hora_fin')

        
        horarios_posibles = []
        hora_actual = inicio_dia
        
        while hora_actual < fin_dia:
            es_disponible = True
            
            # 1. Verificar colisión con citas agendadas
            for cita_inicio, duracion in citas_agendadas:
                cita_fin = cita_inicio + timedelta(minutes=duracion)
                if hora_actual < cita_fin and (hora_actual + timedelta(minutes=DURACION_CITA)) > cita_inicio:
                    es_disponible = False
                    break
                
            # 2. Verificar colisión con bloqueos
            if es_disponible:
                for bloqueo_inicio, bloqueo_fin in bloqueos:
                    if hora_actual < bloqueo_fin and (hora_actual + timedelta(minutes=DURACION_CITA)) > bloqueo_inicio:
                        es_disponible = False
                        break
                
            
            if es_disponible and (hora_actual + timedelta(minutes=DURACION_CITA)) <= fin_dia:
                horarios_posibles.append({
                    'hora': hora_actual.strftime('%H:%M'),
                    'valor': hora_actual.isoformat(), 
                })
            
            hora_actual += timedelta(minutes=DURACION_CITA)
            
        return JsonResponse({'horarios': horarios_posibles})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ----------------------------------------------------------------------
# Vistas del Kinesiólogo
# ----------------------------------------------------------------------

class KinesiologoDashboardView(LoginRequiredMixin, View):
    template_name = 'kine_dash.html' 
    
    def get_kinesiologo(self, user):
        """Intenta obtener el objeto Kinesiologo asociado al User."""
        try:
            return Kinesiologo.objects.get(perfil__user=user)
        except Kinesiologo.DoesNotExist:
            return None

    def get(self, request):
        if request.user.perfil.rol != KINESIOLOGO:
            messages.error(request, "Acceso no autorizado al dashboard de Kinesiólogo.")
            return redirect('index') 
            
        kine = self.get_kinesiologo(request.user)
        if not kine:
            messages.error(request, "Perfil de Kinesiólogo no encontrado.")
            return redirect('index')
            
        hoy = timezone.localdate()
        
        # OBTENER CITAS: El cambio clave es excluir solo las FINALIZADAS
        # Esto permite que las citas CANCELADAS aparezcan en la lista del Kine.
        citas_proximas = Cita.objects.filter(
            kinesiologo=kine,
            fecha_hora_inicio__date__gte=hoy
        ).exclude(
            # ✅ CORRECCIÓN: Usamos CITA_FINALIZADA, NO CITA_CANCELADA.
            estado=CITA_FINALIZADA 
        ).order_by('fecha_hora_inicio')

        bloqueos = BloqueoHorario.objects.filter(
            kinesiologo=kine,
            fecha_hora_inicio__date__gte=hoy
        ).order_by('fecha_hora_inicio')

        context = {
            'citas_proximas': citas_proximas,
            'bloqueos': bloqueos,
            'kinesiologo': kine,
            'fecha_hoy': hoy,
        }
        return render(request, self.template_name, context)

    # Lógica POST para cambiar estado de citas (Confirmar, Finalizar, Cancelar)
    def post(self, request):
        cita_pk = request.POST.get('cita_pk')
        accion = request.POST.get('accion')
        
        cita = get_object_or_404(Cita, pk=cita_pk)
        
        if cita.kinesiologo.perfil.user != request.user:
            messages.error(request, "No tienes permiso para modificar esta cita.")
            return redirect(reverse('citas:kinesiologo_dashboard'))

        try:
            if accion == 'confirmar':
                cita.estado = CITA_CONFIRMADA
                messages.success(request, f"Cita con {cita.paciente.nombre} confirmada.")
            elif accion == 'cancelar':
                cita.estado = CITA_CANCELADA
                messages.warning(request, f"Cita con {cita.paciente.nombre} cancelada.")
            elif accion == 'finalizar' and cita.estado != CITA_FINALIZADA:
                # Redirigir a la vista de Nota Clínica para que se complete el flujo
                return redirect(reverse('evaluaciones:crear_nota_clinica', kwargs={'cita_pk': cita.pk}))

            # Guardar el estado si fue confirmar o cancelar
            if accion in ['confirmar', 'cancelar']:
                cita.save()

        except Exception as e:
            messages.error(request, f"Error al procesar la acción: {e}")

        return redirect(reverse('citas:kinesiologo_dashboard'))


# citas/views.py (función gestionar_bloqueos)

@login_required
@transaction.atomic
def gestionar_bloqueos(request):
    """Permite al Kinesiólogo añadir o eliminar bloques de horario."""
    
    # 1. Validación de Rol
    if request.user.perfil.rol != KINESIOLOGO:
        messages.error(request, "Acceso no autorizado.")
        return redirect('index')

    # 2. OBTENCIÓN SEGURA DEL KINESIOLOGO
    try:
        kine = Kinesiologo.objects.get(perfil__user=request.user)
    except Kinesiologo.DoesNotExist:
        messages.error(request, "Error de perfil: Tu cuenta no está asociada a un perfil de Kinesiólogo válido.")
        return redirect(reverse('citas:kinesiologo_dashboard')) 

    # --- Inicialización de variables para el GET ---
    form = BloqueoHorarioForm() 
    bloqueos_futuros = BloqueoHorario.objects.none() 

    # ----------------------------------------------------------------------
    # 3. MANEJO DE POST (CREAR O ELIMINAR)
    # ----------------------------------------------------------------------
    if request.method == 'POST':
        if 'add_bloqueo' in request.POST:
            form = BloqueoHorarioForm(request.POST) 
            if form.is_valid():
                bloqueo = form.save(commit=False)
                bloqueo.kinesiologo = kine 
                
                # Validación de traslape con citas
                traslape_citas = Cita.objects.filter(
                    kinesiologo=kine,
                    fecha_hora_inicio__lt=bloqueo.fecha_hora_fin,
                    fecha_hora_fin__gt=bloqueo.fecha_hora_inicio,
                    estado__in=[CITA_PENDIENTE, CITA_CONFIRMADA]
                )
                
                if traslape_citas.exists():
                    messages.error(request, "El bloqueo se traslapa con citas ya agendadas.")
                else:
                    bloqueo.save()
                    messages.success(request, "Horario bloqueado con éxito.")
            else:
                messages.error(request, "Error en el formulario de bloqueo. Por favor, revisa las fechas y horas.")
                
        elif 'delete_bloqueo' in request.POST:
            bloqueo_pk = request.POST.get('bloqueo_pk')
            if bloqueo_pk: 
                try:
                    bloqueo = BloqueoHorario.objects.get(pk=bloqueo_pk, kinesiologo=kine)
                    bloqueo.delete()
                    messages.success(request, "Bloqueo de horario eliminado.")
                except BloqueoHorario.DoesNotExist:
                    messages.error(request, "El bloqueo no existe o no tienes permiso para eliminarlo.")
                except Exception as e:
                    messages.error(request, f"Error al intentar eliminar el bloqueo: {e}")
            else:
                messages.error(request, "ID de bloqueo no proporcionado.")

        # Redirigir siempre después del POST
        return redirect(reverse('citas:gestionar_bloqueos'))
    
    # ----------------------------------------------------------------------
    # 4. MANEJO DE GET (MOSTRAR LA PÁGINA) 
    # ----------------------------------------------------------------------
    hoy = timezone.localdate()
    
    try:
        # Filtra los bloques para el Kinesiólogo obtenido
        bloqueos_futuros = BloqueoHorario.objects.filter(
            kinesiologo=kine,
            fecha_hora_inicio__date__gte=hoy
        ).order_by('fecha_hora_inicio')
        
    except ObjectDoesNotExist:
        messages.error(request, "Error de datos: Se encontraron bloques con referencias a Kinesiólogos eliminados. Contacta a soporte.")
        bloqueos_futuros = BloqueoHorario.objects.none()
    except Exception as e:
        messages.error(request, f"Error inesperado al listar bloqueos: {e}")
        bloqueos_futuros = BloqueoHorario.objects.none()

    context = {
        'form': form,
        'bloqueos_futuros': bloqueos_futuros
    }
    return render(request, 'kine_bloq.html', context)