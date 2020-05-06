from django import template
from datetime import datetime, timedelta
from django.utils import timezone

now = timezone.now()
register = template.Library()
@register.filter
def less_than_two_days_old(value):
    return (value.replace(tzinfo=None) - timedelta(hours=4)) > (datetime.now() - timedelta(days=2))

@register.filter
def past(value):
    return (value.replace(tzinfo=None) - timedelta(hours=4)) < datetime.now()

@register.filter
def future(value):
    return (value.replace(tzinfo=None) - timedelta(hours=4)) > datetime.now()