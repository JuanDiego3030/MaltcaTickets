from django import template
register = template.Library()

@register.filter
def get(value, arg):
    """Gets an item from a dict."""
    try:
        return value[arg]
    except (KeyError, TypeError):
        return ''
