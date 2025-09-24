from .models import CompanyProfile

def company_profile_processor(request):
    company_profile = CompanyProfile.objects.first()
    return {'company_profile': company_profile}