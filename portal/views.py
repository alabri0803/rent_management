from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from dashboard.models import Lease, Tenant

class PortalDashboardView(LoginRequiredMixin, TemplateView):
  template_name = 'portal/dashboard.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    try:
      tenant = Tenant.objects.get(user=self.request.user)
      leases = Lease.objects.filter(tenant=tenant, status__in=['active', 'expired_soon']).first()
      context['leases'] = leases
      if leases:
          context['payments'] = leases.payments.all()
    except Tenant.DoesNotExist:
       context['error'] = 'لا يوجد ملف مستأجر مرتبط بحسابك'
    return context