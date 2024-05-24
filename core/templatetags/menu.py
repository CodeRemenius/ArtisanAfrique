from django import template

from core.models import Category

register = template.Library()

@register.inclusion_tag('core/menu.html')
def menu():
    categories = Category.objects.all()[:3]

    return {'categories': categories}