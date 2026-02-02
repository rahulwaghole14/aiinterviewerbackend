from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter
def format_markdown(text):
    """
    Simple markdown formatter for PDF templates
    Converts basic markdown to HTML for PDF rendering
    """
    if not text:
        return ""
    
    # Convert markdown to basic HTML
    text = text.replace('**', '<strong>').replace('**', '</strong>')
    text = text.replace('*', '<em>').replace('*', '</em>')
    
    # Convert line breaks to <br>
    text = text.replace('\n', '<br>')
    
    # Convert headers
    text = re.sub(r'^### (.*)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.*)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.*)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    
    # Convert lists
    text = re.sub(r'^- (.*)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    text = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', text, flags=re.MULTILINE | re.DOTALL)
    
    return mark_safe(text)

@register.filter
def linebreaksbr(text):
    """
    Convert line breaks to <br> tags
    """
    if not text:
        return ""
    return mark_safe(text.replace('\n', '<br>'))
