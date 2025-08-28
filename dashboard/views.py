from django.shortcuts import render, redirect, get_object_or_404
from .models import Lease
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .forms import LeaseForm
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from dateutil.relativedelta import relativedelta
from django.utils import timezone

class LeaseListView(ListView):
  model = Lease
  template_name = 'dashboard/lease_list.html'
  context_object_name = 'leases'
  paginate_by = 10

  def get_queryset(self):
    for lease in Lease.objects.all():
      lease.save().update_status()
    return Lease.objects.all().order_by('-start_date')

class LeaseDetailView(DetailView):
  model = Lease
  template_name = 'dashboard/lease_detail.html'
  context_object_name = 'lease'

class LeaseCreateView(CreateView):
  model = Lease
  form_class = LeaseForm
  template_name = 'dashboard/lease_form.html'
  success_url = reverse_lazy('lease_list')

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['title'] = _('إضافة عقد جديد')
    return context

  def form_valid(self, form):
    messages.success(self.request, _('تمت إضافة العقد بنجاح!'))
    return super().form_valid(form)

class LeaseUpdateView(UpdateView):
  model = Lease
  form_class = LeaseForm
  template_name = 'dashboard/lease_form.html'
  success_url = reverse_lazy('lease_list')

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['title'] = _('تعديل العقد')
    return context

  def form_valid(self, form):
    messages.success(self.request, _('تم تحديث العقد بنجاح!'))
    return super().form_valid(form)

class LeaseDeleteView(DeleteView):
  model = Lease
  template_name = 'dashboard/lease_confirm_delete.html'
  success_url = reverse_lazy('lease_list')

  def form_valid(self, form):
    messages.success(self.request, _('تم حذف العقد بنجاح!'))
    return super().form_valid(form)

def renew_lease(request, pk):
  original_lease = get_object_or_404(Lease, pk=pk)
  if request.method == 'POST':
    duration = request.POST.get('duration')
    new_start_date = original_lease + relativedelta(days=1)
    if duration == '1y':
      new_end_date = new_start_date + relativedelta(years=1, days=-1)
    elif duration == '6m':
      new_end_date = new_start_date + relativedelta(months=6, days=-1)
    elif duration == '3m':
      new_end_date = new_start_date + relativedelta(months=3, days=-1)
    else:
      new_end_date = request.POST.get('manual_date')
      if not new_end_date:
        messages.error(request, _('الرجا إدخال تاريخ انتهاء صحيح'))
        return redirect('renew_lease', pk=pk)
    new_lease = Lease.objects.create(
      unit=original_lease.unit,
      tenant=original_lease.tenant,
      contract_number=f"{original_lease.contract_number}-R",
      monthly_rent=original_lease.monthly_rent,
      start_date=new_start_date,
      end_date=new_end_date,
    )
    original_lease.status = 'expired'
    original_lease.save()
    messages.success(request, _('تم تجديد العقد بنجاح!'))
    return redirect('lease_list', pk=new_lease.pk)
  return render(request, 'dashboard/lease_renew.html', {'lease': original_lease})