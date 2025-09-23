from .models import CompanyProfile

def company_details(request):
  return {'company': CompanyProfile.get_solo()}