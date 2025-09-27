from django.shortcuts import render
from django.views.generic import TemplateView, ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from dashboard.models import Lease, Tenant, MaintenanceRequest
from dashboard.forms import MaintenanceRequestForm

class PortalDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'portal/dashboard.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            tenant = Tenant.objects.get(user=self.request.user)
            lease = Lease.objects.filter(tenant=tenant, status__in=['active', 'expiring_soon']).order_by('-start_date').first()
            context['tenant'] = tenant
            context['lease'] = lease
            if lease:
                context['payment_summary'] = lease.get_payment_summary()
                context['documents'] = lease.documents.all()
                context['maintenance_requests'] = MaintenanceRequest.objects.filter(lease=lease).order_by('-reported_date')[:5]
        except Tenant.DoesNotExist:
            context['error'] = _("لا يوجد ملف مستأجر مرتبط بحسابك.")
        return context

class MaintenanceRequestListView(LoginRequiredMixin, ListView):
    model = MaintenanceRequest; template_name = 'portal/maintenance_list.html'; context_object_name = 'requests'
    def get_queryset(self):
        try:
            tenant = Tenant.objects.get(user=self.request.user)
            return MaintenanceRequest.objects.filter(lease__tenant=tenant)
        except Tenant.DoesNotExist:
            return MaintenanceRequest.objects.none()

class MaintenanceRequestCreateView(LoginRequiredMixin, CreateView):
    model = MaintenanceRequest; form_class = MaintenanceRequestForm; template_name = 'portal/maintenance_form.html'; success_url = reverse_lazy('maintenance_list')
    def form_valid(self, form):
        try:
            tenant = Tenant.objects.get(user=self.request.user)
            active_lease = Lease.objects.filter(tenant=tenant, status__in=['active', 'expiring_soon']).first()
            if not active_lease:
                messages.error(self.request, _("لا يمكنك إنشاء طلب صيانة بدون عقد نشط."))
                return super().form_invalid(form)
            form.instance.lease = active_lease
            messages.success(self.request, _("تم إرسال طلب الصيانة بنجاح!"))
            return super().form_valid(form)
        except Tenant.DoesNotExist:
            messages.error(self.request, _("حسابك غير مرتبط بملف مستأجر."))
            return super().form_invalid(form)