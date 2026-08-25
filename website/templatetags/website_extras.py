"""Template helpers used across the public site."""
from django import template
from django.template.defaultfilters import stringfilter
import re

register = template.Library()

# Matches "field | value" rows in the plain-text specifications field.
_SPEC_SPLIT = re.compile(r'\s*\|\s*')


@register.filter
@stringfilter
def spec_rows(value):
    """Turn a ``key | value``-per-line block into a list of (key, value) pairs."""
    rows = []
    for line in value.splitlines():
        line = line.strip()
        if not line:
            continue
        if '|' in line:
            key, _, val = line.partition('|')
            rows.append((key.strip(), val.strip()))
        else:
            rows.append(('', line))
    return rows


@register.filter
def file_ext(value):
    """Return the uppercase extension of a FileField's name, e.g. ``PDF``."""
    if not value:
        return ''
    name = getattr(value, 'name', str(value))
    dot = name.rfind('.')
    return name[dot + 1:].upper() if dot != -1 else ''
