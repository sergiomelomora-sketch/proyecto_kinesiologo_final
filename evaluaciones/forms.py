# evaluaciones/forms.py

from django import forms
from .models import NotaClinica

class NotaClinicaForm(forms.ModelForm):
    class Meta:
        model = NotaClinica
        fields = [
            'diagnostico_subjetivo', 
            'diagnostico_objetivo', 
            'analisis_y_plan'
        ]
        
        widgets = {
            'diagnostico_subjetivo': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'diagnostico_objetivo': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'analisis_y_plan': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }
        
        labels = {
            'diagnostico_subjetivo': 'Diagnóstico Subjetivo (S)',
            'diagnostico_objetivo': 'Diagnóstico Objetivo (O)',
            'analisis_y_plan': 'Análisis y Plan (A/P)',
        }