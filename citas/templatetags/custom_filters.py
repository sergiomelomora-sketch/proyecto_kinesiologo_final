# citas/templatetags/custom_filters.py

from django import template

# Esta línea registra la librería con Django
register = template.Library()

# Filtro simple (necesario para que la librería no esté vacía)
@register.filter
def default_if_none(value, default_value="N/A"):
    """Devuelve el valor si no es None, de lo contrario devuelve el valor predeterminado."""
    return value if value is not None else default_value