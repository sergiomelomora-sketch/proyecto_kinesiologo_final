# citas/forms.py

from django import forms
from .models import Cita, BloqueoHorario # <-- BloqueoHorario y Cita importados
from usuarios.models import Kinesiologo, Paciente 
from django.contrib.auth import get_user_model
from django.utils import timezone # Necesario para la validación de fecha/hora


User = get_user_model()


class CitaForm(forms.ModelForm):
    
    kinesiologo = forms.ModelChoiceField(
        queryset=Kinesiologo.objects.all(),
        label="Seleccionar Kinesiólogo",
        empty_label="--- Seleccione un Kinesiólogo ---",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Cita
        
        fields = ['kinesiologo', 'fecha_hora_inicio', 'motivo'] 
        
        widgets = {
            'fecha_hora_inicio': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'motivo': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Breve descripción del motivo de la cita.'}),
        }

        
        labels = {
            'fecha_hora_inicio': 'Fecha y Hora',
            'motivo': 'Motivo de la Cita',
        }


class RegistroPacienteForm(forms.ModelForm):
    
    email = forms.EmailField(label="Correo Electrónico (Para notificaciones)", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = Paciente
        fields = [
            'rut', 
            'nombre', 
            'apellido', 
            'telefono', 
            'direccion', 
            'prevision', 
            'antecedentes_medicos'
        ] 
        widgets = {
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 11111111-1'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 912345678'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'prevision': forms.Select(attrs={'class': 'form-control'}),
            'antecedentes_medicos': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Alergias, cirugías previas, condiciones crónicas, etc.'}),
        }
        labels = {
            'rut': 'RUT (será tu usuario de acceso)',
            'telefono': 'Teléfono Celular (últimos 4 dígitos serán tu clave)',
        }
        
    def clean_rut(self):
        
        rut = self.cleaned_data.get('rut')
        # Limpieza básica para evitar errores de duplicidad antes de la creación del User
        if User.objects.filter(username=rut).exists():
             raise forms.ValidationError("Ya existe un usuario con este RUT.")
        if Paciente.objects.filter(rut=rut).exists():
            raise forms.ValidationError("Ya existe un paciente registrado con este RUT.")
        return rut


# >>>>>>>>>>>>>>>>>> FORMULARIO FALTANTE AÑADIDO <<<<<<<<<<<<<<<<<<<<

class BloqueoHorarioForm(forms.ModelForm):
    """
    Formulario para que el Kinesiólogo cree un bloqueo de horario.
    """
    class Meta:
        model = BloqueoHorario
        # No incluimos kinesiologo aquí, ya que se asigna automáticamente en la vista.
        fields = ['fecha_hora_inicio', 'fecha_hora_fin', 'motivo']
        widgets = {
            'fecha_hora_inicio': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'fecha_hora_fin': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'motivo': forms.TextInput(attrs={'placeholder': 'Ej: Vacaciones, Reunión, Trámites', 'class': 'form-control'}),
        }
        labels = {
             'fecha_hora_inicio': 'Inicio del Bloqueo',
             'fecha_hora_fin': 'Fin del Bloqueo',
        }
        
    def clean(self):
        cleaned_data = super().clean()
        inicio = cleaned_data.get('fecha_hora_inicio')
        fin = cleaned_data.get('fecha_hora_fin')

        if inicio and fin:
            if inicio >= fin:
                raise forms.ValidationError("La fecha y hora de fin debe ser posterior a la de inicio.")
            # Permitir bloqueo pasado para fines de testeo, pero idealmente se limita:
            # if inicio < timezone.now(): 
            #     raise forms.ValidationError("No se puede bloquear un horario en el pasado.")
        
        return cleaned_data