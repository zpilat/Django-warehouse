from django import template
from ..models import Varianty

register = template.Library()

@register.filter(name='get_attribute')
def get_attribute(value, arg):
    """ Získá atribut podle jeho názvu z objektu a zobrazí 'ANO' nebo 'NE' pro boolean hodnoty. """
    result = getattr(value, arg, 'Atribut neexistuje')
    if isinstance(result, bool):
        return "ANO" if result else "NE"
    return result


@register.filter
def url_remove_param(querystring, params):
    params = params.split(',')
    new_querystring = '&'.join(
        f"{key}={value}"
        for part in querystring.split('&')
        if '=' in part and (key := part.split('=')[0]) not in params and (value := part.split('=')[1])
    )
    return new_querystring


@register.filter
def get_instance(queryset, pk):
    try:
        return queryset.get(pk=pk)
    except (Varianty.DoesNotExist, TypeError, ValueError):
        return 'Instance neexistuje'
