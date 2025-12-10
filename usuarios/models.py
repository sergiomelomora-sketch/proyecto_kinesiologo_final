# usuarios/models.py

from django.db import models
from django.contrib.auth.models import User 


KINESIOLOGO = 1
PACIENTE = 2
ROLES_CHOICES = (
    (KINESIOLOGO, 'Kinesiólogo'),
    (PACIENTE, 'Paciente'),
)

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
     
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    
    rol = models.PositiveSmallIntegerField(choices=ROLES_CHOICES, default=PACIENTE)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        
        return f'{self.nombre} {self.apellido} ({self.get_rol_display()})'

class Kinesiologo(models.Model):
    perfil = models.OneToOneField(Perfil, on_delete=models.CASCADE)
    especialidad = models.CharField(max_length=100) 
    licencia = models.CharField(max_length=50, unique=True)

    def __str__(self):
        
        return str(self.perfil)



class Paciente(models.Model):
    
    rut = models.CharField(max_length=12, unique=True,null=True, blank=True)
    telefono = models.CharField(max_length=15)
    perfil = models.OneToOneField(Perfil, on_delete=models.CASCADE) 

    
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    
    
    PREVISION_CHOICES = [
        ('F', 'FONASA'),
        ('I', 'ISAPRE'),
        ('P', 'Particular'),
    ]
    prevision = models.CharField(max_length=1, choices=PREVISION_CHOICES, default='F')
    
    
    antecedentes_medicos = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Antecedentes Médicos Relevantes"
    )
    
    
    
    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.rut})"