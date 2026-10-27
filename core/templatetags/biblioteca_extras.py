from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def querystring(context, **kwargs):
    """Construye un query string conservando los filtros actuales."""
    request = context.get("request")
    params = request.GET.copy() if request else {}
    for key, value in kwargs.items():
        if value in (None, ""):
            params.pop(key, None)
        else:
            params[key] = value
    if "page" not in kwargs:
        params.pop("page", None)
    return params.urlencode()


@register.filter
def pluralize_es(value, singular="registro"):
    try:
        cantidad = int(value)
    except (TypeError, ValueError):
        return singular
    return singular if cantidad == 1 else f"{singular}s"
