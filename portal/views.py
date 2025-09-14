from django.views.generic import TemplateView, ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages

from dashboard.models import Lease, Tenant, MaintenanceRequest
from dashboard.forms import MaintenanceRequestForm

class PortalDashboardView(LoginRequiredMixin, TemplateView):
  template_name = 'portal/dashboard.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    try:
      tenant = Tenant.objects.get(user=self.request.user)
      lease = Lease.objects.filter(tenant=tenant, status__in=['active', 'expired_soon']).order_by('-start_date').first
      context['tenant'] = tenant
      context['leases'] = lease
      if lease:
          context['payments'] = lease.payments.all()
          context['documents'] = lease.documents.all()
    except Tenant.DoesNotExist:
       context['error'] = 'لا يوجد ملف مستأجر مرتبط بحسابك'
    return context

class MaintenanceRequestListView(LoginRequiredMixin, ListView):
  model = MaintenanceRequest
  template_name = 'portal/maintenance_list.html'
  context_object_name = 'requests'

  def get_queryset(self):
    try:
      tenant = Tenant.objects.get(user=self.request.user)
      return MaintenanceRequest.objects.filter(lease__tenant=tenant)
    except Tenant.DoesNotExist:
      return MaintenanceRequest.objects.none()

class MaintenanceRequestCreateView(LoginRequiredMixin, CreateView):
  model = MaintenanceRequest
  form_class = MaintenanceRequestForm
  template_name = 'portal/maintenance_form.html'
  success_url = reverse_lazy('maintenance_request_list')

  def form_valid(self, form):
    try:
      tenant = Tenant.objects.get(user=self.request.user)
      active_lease = Lease.objects.filter(tenant=tenant, status__in=['active', 'expired_soon']).first()
      if not active_lease:
        messages.error(self.request, 'لا يمكنك إنشاء طلب صيانة بدون عقد نشط.')
        return self.form_invalid(form)
      form.instance.lease = active_lease
      messages.success(self.request, 'تم إرسال طلب الصيانة بنجاح.')
      return super().form_valid(form)
    except Tenant.DoesNotExist:
      messages.error(self.request, 'حسابك غير مرتبط بملف مستأجر.')
      return self.form_invalid(form)