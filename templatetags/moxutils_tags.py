from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from datetime import datetime
import random

register = template.Library()

@register.filter
def parse_gender(value):
    return ["M","F"][value-1]

@register.filter
def parse_type_of_cage(value):
    if (value==2): return "Yes"
    return "No"

@register.filter
def parse_date(value):
    return value.strftime("%d-%m-%Y")


@register.filter
def obj_lookup(obj, prop):
    if hasattr(obj, prop):
        return getattr(obj, prop)

@register.filter
def lookup(dictionary, index):
	try:
		return dictionary[index]
	except KeyError:
		return None

@register.filter
def multiply(value, param):
	v = float(value)
	return v*param

@register.filter
def divide(value, param):
	v = float(value)
	return v/param

@register.filter
def percent(value):
	if value is not None:
		v = float(value)*100.
		return "%.0f" % v
	else:
		return "ND"

@register.filter
def None2ND(value):
	if value is not None:
		return value
	else:
		return "ND"

@stringfilter
@register.filter
def nbspaces(value, autoescape=None):
    if autoescape:
        esc = conditional_escape
    else:
        esc = lambda x: x
    return mark_safe(esc(value).replace(" ","&nbsp;"))
nbspaces.needs_autoescape = True

@register.filter
def truncatewords_by_chars(value, arg):
    """Truncate the text when it exceeds a certain number of characters.
    Delete the last word only if partial.
    Adds '...' at the end of the text.
    
    Example:
    
        {{ text|truncatewords_by_chars:25 }}
    """
    try:
        length = int(arg)
    except ValueError:
        return value
    
    if len(value) > length:
        if value[length:length + 1].isspace():
            return value[:length].rstrip() + '...'
        else:
            return value[:length].rsplit(' ', 1)[0].rstrip() + '...'
    else:
        return value

@register.filter
def shuffle(arg):
    tmp = list(arg[:])
    random.shuffle(tmp)
    return tmp
