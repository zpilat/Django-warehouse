from django import template

register = template.Library()

@register.filter(name='get_attribute')
def get_attribute(value, arg):
    """ Získá atribut podle jeho názvu z objektu a zobrazí 'ANO' nebo 'NE' pro boolean hodnoty. """
    result = getattr(value, arg, 'Atribut neexistuje')
    if isinstance(result, bool):
        return "ANO" if result else "NE"
    return result


