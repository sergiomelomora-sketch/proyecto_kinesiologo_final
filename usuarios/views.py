from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.views.decorators.http import require_http_methods
from django.views import View
from django.urls import reverse
from django.contrib.auth import get_user_model
import re 


# >>>>>>>>>>>>>>>>>> CORRECCIÓN AQUÍ <<<<<<<<<<<<<<<<<<<<
# Importamos la constante KINESIOLOGO y el modelo Kinesiologo
from .models import Paciente, Perfil, Kinesiologo, KINESIOLOGO, PACIENTE
from citas.forms import RegistroPacienteForm

User = get_user_model()


def clean_rut(rut_string):
    """Limpia el RUT de puntos, guiones y espacios para la búsqueda en BD."""
    if not rut_string:
        return ""
    
    rut_string = rut_string.replace('.', '').replace('-', '').upper().strip()
    
    return re.sub(r'[^0-9K]', '', rut_string)


def inicio_usuarios(request):
    return render(request, 'usuarios/inicio.html')


def index(request):
    """
    Página principal que sirve como dashboard para el paciente logueado
    o como página de bienvenida si no lo está.
    """
    # Si el usuario está autenticado, lo redirigimos a la agenda.
    if request.user.is_authenticated:
        # AQUI HAY UN PUNTO DE MEJORA: debería redirigir a kinesiologo_dashboard si es kine
        return redirect('citas:agenda') 

    return render(request, 'index.html', {'usuario': request.user})


def logout_view(request):
    """
    Cierra la sesión del usuario actual y lo redirige a la página de inicio.
    """
    logout(request)
    messages.info(request, "Sesión cerrada correctamente.")
    return redirect('index')


@require_http_methods(["GET", "POST"])
def autenticar_paciente(request):
    """
    Vista personalizada para autenticar usando RUT y los últimos 4 dígitos del celular.
    """
    if request.method == 'POST':
        rut_formato_sucio = request.POST.get('rut')
        clave_celular = request.POST.get('clave_celular')

        
        rut = clean_rut(rut_formato_sucio)

        if not rut or not clave_celular:
            messages.error(request, "Debe ingresar el RUT y la clave celular.")
            
            return render(request, 'usuarios_login.html', {'rut': rut_formato_sucio, 'clave_celular': clave_celular})

        try:
            
            paciente = Paciente.objects.get(rut=rut)

            
            telefono = paciente.telefono if paciente.telefono else ""
            ultimos_4_digitos = telefono[-4:] if len(telefono) >= 4 else ""

            
            if clave_celular == ultimos_4_digitos:
                
                login(request, paciente.perfil.user)

                messages.success(request, f"¡Bienvenido/a, {paciente.nombre}!")
                
                
                return redirect('citas:agenda') 
                
            else:
                messages.error(request, "RUT o clave celular incorrectos.")

        except Paciente.DoesNotExist:
            messages.error(request, "RUT no encontrado en el sistema. ¿Necesitas registrarte?")
        except AttributeError:
            messages.error(request, "Error de sistema: El paciente no tiene un usuario asociado.")
        except Exception as e:
            messages.error(request, f"Ocurrió un error inesperado. {e}")

        
        return render(request, 'usuarios_login.html', {'rut': rut_formato_sucio, 'clave_celular': clave_celular})

    
    return render(request, 'usuarios_login.html')


class RegistroPacienteView(View):
    template_name = 'usuarios_registro.html'

    def get(self, request):
        """Muestra el formulario de registro vacío."""
        form = RegistroPacienteForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        """Procesa el envío del formulario y crea el User y el Paciente."""
        form = RegistroPacienteForm(request.POST)

        if form.is_valid():
            try:
                
                rut = form.cleaned_data['rut']
                email = form.cleaned_data['email']
                nombre = form.cleaned_data['nombre']
                apellido = form.cleaned_data['apellido']
                telefono = form.cleaned_data['telefono']

                
                clave_inicial = telefono[-4:] if len(telefono) >= 4 else "0000"

                
                user = User.objects.create_user(
                    username=rut,
                    email=email,
                    first_name=nombre,
                    last_name=apellido,
                    password=clave_inicial
                )

                
                perfil, created = Perfil.objects.get_or_create(user=user)

                
                paciente = form.save(commit=False)
                paciente.perfil = perfil
                paciente.save()

                messages.success(
                    request,
                    f"¡Registro exitoso! Ya puedes iniciar sesión con tu RUT y la clave **{clave_inicial}** (los 4 últimos dígitos de tu celular)."
                )

                
                return redirect(reverse('usuarios:autenticar_paciente'))

            except Exception as e:
                
                if 'user' in locals():
                    user.delete()
                messages.error(request, f"Error al crear el perfil de paciente. Contacte a soporte. Error: {e}")

        return render(request, self.template_name, {'form': form})
    
# usuarios/views.py (PEGA ESTO AL FINAL DEL ARCHIVO)

@require_http_methods(["GET", "POST"])
def autenticar_kinesiologo(request):
    """
    Vista de login específica para Kinesiólogos.
    Asume que usan un username (RUT) y una contraseña proporcionada.
    """
    if request.method == 'POST':
        username = request.POST.get('username') # Asumimos que es el RUT
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # 1. Verificar si el usuario es un Kinesiólogo
            try:
                # La constante KINESIOLOGO ahora está definida gracias a la importación
                if user.perfil.rol == KINESIOLOGO:
                    login(request, user)
                    messages.success(request, f"Bienvenido/a Kine {user.first_name}.")
                    # Redirigir al Dashboard del Kinesiólogo
                    return redirect('citas:kinesiologo_dashboard')
                else:
                    # El usuario existe, pero no es un Kinesiólogo
                    messages.error(request, "Acceso denegado. Esta cuenta no tiene rol de Kinesiólogo.")
                    return render(request, 'usuarios_login_kine.html') # Usaremos un template específico
            except AttributeError:
                messages.error(request, "Error de perfil. Contacte a soporte.")
                return render(request, 'usuarios_login_kine.html')
        else:
            messages.error(request, "Credenciales incorrectas o usuario no activo.")

    # Renderizar el formulario de login (crea este template simple)
    return render(request, 'usuarios_login_kine.html')