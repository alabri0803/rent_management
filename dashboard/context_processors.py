from .models import Company

def company_details(request):
  return {'company': Company.load()}