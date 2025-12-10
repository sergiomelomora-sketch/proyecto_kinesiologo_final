# citas/models.py

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from usuarios.models import Kinesiologo, Paciente 


# -----------------------------------------------------------
# CONSTANTES DE ESTADO (Ajustadas para coincidir con las vistas)
# -----------------------------------------------------------

CITA_PENDIENTE = 'PENDIENTE'
CITA_CONFIRMADA = 'CONFIRMADA'
CITA_FINALIZADA = 'FINALIZADA'
CITA_CANCELADA = 'CANCELADA'

ESTADOS_CITA = [
    (CITA_PENDIENTE, 'Pendiente de Confirmación'),
    (CITA_CONFIRMADA, 'Confirmada'),
    (CITA_FINALIZADA, 'Finalizada'),
    (CITA_CANCELADA, 'Cancelada'),
]

# -----------------------------------------------------------
# MODELO CITA (Con ajustes de constantes)
# -----------------------------------------------------------

class Cita(models.Model):
    """Modelo para representar una cita médica."""
    
    kinesiologo = models.ForeignKey(Kinesiologo, on_delete=models.PROTECT, related_name='citas_atendidas')
    paciente = models.ForeignKey(Paciente, on_delete=models.PROTECT, related_name='citas_solicitadas')
    
    fecha_hora_inicio = models.DateTimeField() 
    duracion_minutos = models.PositiveSmallIntegerField(default=60) 
    motivo = models.TextField(blank=True, null=True)
    
    estado = models.CharField(
        max_length=15, # Aumentar max_length para acomodar 'PENDIENTE' y 'CONFIRMADA'
        choices=ESTADOS_CITA,
        default=CITA_PENDIENTE
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('kinesiologo', 'fecha_hora_inicio') 
        ordering = ['fecha_hora_inicio']
        verbose_name = "Cita"
        verbose_name_plural = "Citas"

    def __str__(self):
        # Usar timezone.localtime para mostrar la hora en la zona local si aplica
        local_time = timezone.localtime(self.fecha_hora_inicio)
        return f"Cita de {self.paciente} con {self.kinesiologo} el {local_time.strftime('%d-%m-%Y %H:%M')}"
        
    @property
    def fecha_hora_fin(self):
        """Calcula la hora de fin de la cita."""
        return self.fecha_hora_inicio + timezone.timedelta(minutes=self.duracion_minutos)


# -----------------------------------------------------------
# MODELO BLOQUEO HORARIO (El modelo que faltaba)
# -----------------------------------------------------------

class BloqueoHorario(models.Model):
    """
    Modelo para que el Kinesiólogo bloquee franjas de tiempo en su agenda.
    """
    kinesiologo = models.ForeignKey(Kinesiologo, on_delete=models.CASCADE, related_name='bloqueos')
    fecha_hora_inicio = models.DateTimeField()
    fecha_hora_fin = models.DateTimeField()
    motivo = models.CharField(max_length=255, blank=True, null=True, 
                              help_text="Ej. Vacaciones, Trámites Personales, Conferencia.")

    class Meta:
        verbose_name = "Bloqueo de Horario"
        verbose_name_plural = "Bloqueos de Horarios"
        ordering = ['fecha_hora_inicio']
        
    def __str__(self):
        # Muestra el rango de fechas en la zona horaria del usuario
        inicio_local = timezone.localtime(self.fecha_hora_inicio).strftime('%Y-%m-%d %H:%M')
        fin_local = timezone.localtime(self.fecha_hora_fin).strftime('%H:%M')
        return f"Bloqueo de {self.kinesiologo.nombre} ({inicio_local} - {fin_local})"

    def clean(self):
        # Validación: inicio debe ser anterior a fin
        if self.fecha_hora_inicio >= self.fecha_hora_fin:
            raise ValidationError({'fecha_hora_fin': 'La hora de fin debe ser posterior a la hora de inicio.'})
        
        # Validación: Bloqueo no debe traslaparse con citas existentes
        if self.kinesiologo:
            traslape_citas = Cita.objects.filter(
                kinesiologo=self.kinesiologo,
                fecha_hora_inicio__lt=self.fecha_hora_fin,
                fecha_hora_inicio__gte=self.fecha_hora_inicio, # Citas que inician durante el bloqueo
                estado__in=[CITA_PENDIENTE, CITA_CONFIRMADA]
            )
            # También verificar citas que terminan durante el bloqueo
            traslape_citas_fin = Cita.objects.filter(
                kinesiologo=self.kinesiologo,
                fecha_hora_inicio__lt=self.fecha_hora_inicio,
                fecha_hora_inicio__range=[self.fecha_hora_inicio - timezone.timedelta(minutes=1), self.fecha_hora_fin],
                estado__in=[CITA_PENDIENTE, CITA_CONFIRMADA]
            )
            
            if traslape_citas.exists() or traslape_citas_fin.exists():
                 # Una validación más simple para evitar complejidad excesiva aquí
                 raise ValidationError("El bloqueo se traslapa con citas ya agendadas (PENDIENTES o CONFIRMADAS).")
