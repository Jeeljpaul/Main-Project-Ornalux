# templatetags/custom_filters.py
from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiplies the value by the argument."""
    try:
        return float(value) * float(arg)
    except (TypeError, ValueError):
        return value

@register.filter(name='sub')
def sub(value, arg):
    """Subtracts the arg from the value"""
    try:
        value = float(value)
        arg = float(arg)
        return value - arg
    except (ValueError, TypeError):
        return ''
