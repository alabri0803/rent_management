from django import template
from dashboard.models import Company

register = template.Library()

@register.simple_tag
def get_company_name():
    company = Company.objects.first()
    return company.name if company else 'Rent Management'

@register.simple_tag
def get_company_logo():
    company = Company.objects.first()
    return company.logo.url if company and company.logo else None