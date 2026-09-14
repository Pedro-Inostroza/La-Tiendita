from django import template

register = template.Library()


@register.filter
def clp(value):
    """Formatea un número como pesos chilenos: puntos cada tres dígitos (Ej. 213890 -> 213.890)."""
    try:
        value = int(value)
    except (TypeError, ValueError):
        return value
    return f"{value:,}".replace(",", ".")
