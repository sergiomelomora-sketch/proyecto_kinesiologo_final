# evaluaciones/models.py

from django.db import models
from citas.models import Cita
from usuarios.models import Kinesiologo, Paciente # Asegúrate de importar Kinesiologo y Paciente

class NotaClinica(models.Model):
    """
    Representa la nota clínica o registro de atención de una sesión (Registro SOAP).
    Está ligada directamente a una Cita y al Kinesiólogo que la crea.
    """
    
    # RELACIONES CLAVE
    
    # 1. Relación con Cita: Usamos OneToOneField para asegurar que cada cita tenga UNA nota.
    #    Usaremos 'primary_key=True' para que el PK de la nota sea el mismo que el de la cita.
    cita = models.OneToOneField(
        Cita, 
        on_delete=models.CASCADE, 
        primary_key=True,
        related_name='nota_clinica',
        verbose_name='Cita Asociada'
    )
    
    # 2. Relación con Kinesiologo: Quién creó la nota. Usamos PROTECT.
    kinesiologo = models.ForeignKey(
        Kinesiologo, 
        on_delete=models.PROTECT, 
        related_name='notas_clinicas_creadas',
        verbose_name='Kinesiólogo'
    )

    # 3. Relación con Paciente: Quién fue atendido.
    #    (Opcional, pero útil si quieres buscar notas por paciente directamente)
    paciente = models.ForeignKey(
        Paciente, 
        on_delete=models.PROTECT, 
        related_name='notas_clinicas',
        verbose_name='Paciente'
    )

    # CAMPOS SOAP (Subjetivo, Objetivo, Análisis, Plan)
    
    diagnostico_subjetivo = models.TextField(
        verbose_name='Diagnóstico Subjetivo (S)',
        help_text='Información reportada por el paciente (síntomas, historial, etc.).'
    )
    diagnostico_objetivo = models.TextField(
        verbose_name='Diagnóstico Objetivo (O)',
        help_text='Hallazgos del examen físico (rangos, fuerza, pruebas especiales, etc.).'
    )
    analisis_y_plan = models.TextField(
        verbose_name='Análisis y Plan (A/P)',
        help_text='Análisis del Kine, objetivos de la sesión y plan de tratamiento futuro.'
    )
    
    # METADATOS
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Nota Clínica'
        verbose_name_plural = 'Notas Clínicas'
        ordering = ['-fecha_creacion']

    def __str__(self):
        # Usamos la relación con la cita para obtener el nombre del paciente
        return f"Nota de {self.cita.paciente.perfil.nombre} - {self.fecha_creacion.date()}"