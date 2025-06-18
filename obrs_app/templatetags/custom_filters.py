# yourapp/templatetags/custom_filters.py
from django import template
from datetime import datetime

register = template.Library()

@register.filter
def calculate_duration(arrival_time, departure_time):
    """Calculate the duration between two datetime objects and return formatted string."""
    duration_seconds = (arrival_time - departure_time).total_seconds()
    hours = int(duration_seconds // 3600)
    minutes = int((duration_seconds % 3600) // 60)
    return f"{hours}h {minutes}m"


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

