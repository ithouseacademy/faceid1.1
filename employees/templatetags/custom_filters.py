# employees/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Dictionary dan kalit bo'yicha qiymat olish"""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def format_minutes(minutes):
    """Daqiqalarni soat va daqiqaga formatlash: 96 -> 1s 36da"""
    try:
        minutes = int(minutes)
        hours = minutes // 60
        mins = minutes % 60
        
        if hours > 0:
            return f"{hours}s {mins}da"
        else:
            return f"{mins}da"
    except:
        return str(minutes)