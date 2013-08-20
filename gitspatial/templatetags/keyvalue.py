from django import template


register = template.Library()


@register.filter
def keyvalue(a_dict, key):
    return a_dict.get(key)
