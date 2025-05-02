from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    """
    Returns the URL-encoded querystring for the current page,
    updating it with the key/value pairs passed to the tag.

    Example usage:
    {% query_transform page=2 %}
    """
    request = context["request"]
    updated = request.GET.copy()
    for k, v in kwargs.items():
        if v is not None:
            updated[k] = v
        else:
            updated.pop(k, 0)
    return updated.urlencode()


@register.filter(name="divide_by")
def divide_by(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0


@register.filter(name="multiply_by")
def multiply_by(value, arg):
    try:
        return float(value) * float(arg)
    except ValueError:
        return 0


@register.filter
def get_item(dictionary, key):
    """Obtiene un valor de un diccionario usando una clave"""
    return dictionary.get(key, key)
