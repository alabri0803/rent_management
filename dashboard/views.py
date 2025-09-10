from django.shortcuts import render, redirect, get_object_or_404
from .models import Lease, Unit, MaintenanceRequest, Document, Expense
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .forms import LeaseForm, MaintenanceRequestUpdateForm, DocumentForm, ExpenseForm
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from dateutil.relativedelta import relativedelta
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count
from django.utils import timezone

def is_staff_user(user):
  return user.is_staff

class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
  def test_func(self):
    return self.request.user.is_staff


class LeaseListView(StaffRequiredMixin, ListView):
  model = Lease
  template_name = 'dashboard/lease_list.html'
  context_object_name = 'leases'
  paginate_by = 10

  def get_queryset(self):
    for lease in Lease.objects.all():
      lease.save() # .save() will call update_status()
    return Lease.objects.all().order_by('-start_date')

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    for lease in Lease.objects.all():
      lease.save()
    active_leases = Lease.objects.filter(status='active')
    expiring_leases = Lease.objects.filter(status='expiring_soon')
    today = timezone.now()
    monthly_expenses = Expense.objects.filter(expense_date__year=today.year, expense_date__month=today.month).aggregate(total=Sum('amount'))['total'] or 0
    #gross_income = context['stats']['expected_monthly_income']
    #context['stats']['monthly_expenses'] = monthly_expenses
    #context['stats']['net_income'] = gross_income - monthly_expenses
    context['stats'] = {
        'active_count': active_leases.count(),
        'expiring_count': expiring_leases.count(),
        'expired_count': Lease.objects.filter(status='expired').count(),
        'total_units': Unit.objects.count(),
        'available_units': Unit.objects.filter(is_available=True).count(),
        'expected_monthly_income': active_leases.aggregate(total=Sum('monthly_rent'))['total'] or 0,
        'monthly_expenses': monthly_expenses,
        'net_income': active_leases.aggregate(total=Sum('monthly_rent'))['total'] or 0 - monthly_expenses
    }
    status_counts = Lease.objects.values('status').annotate(count=Count('status'))
    chart_data ={
        'labels': [],
        'data': [],
      }
    status_display_map = dict(Lease.STATUS_CHOICES)
    for item in status_counts:
        chart_data['labels'].append(status_display_map.get(item['status'],item['status']))
        chart_data['data'].append(item['count'])
    context['chart_data'] = chart_data
    return context



class LeaseDetailView(StaffRequiredMixin, DetailView):
  model = Lease
  template_name = 'dashboard/lease_detail.html'
  context_object_name = 'lease'

class LeaseCreateView(StaffRequiredMixin, CreateView):
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

class LeaseUpdateView(StaffRequiredMixin, UpdateView):
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

class LeaseDeleteView(StaffRequiredMixin, DeleteView):
  model = Lease
  template_name = 'dashboard/lease_confirm_delete.html'
  success_url = reverse_lazy('lease_list')

  def form_valid(self, form):
    messages.success(self.request, _('تم حذف العقد بنجاح!'))
    return super().form_valid(form)

@login_required
@user_passes_test(is_staff_user)
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

class MaintenanceRequestAdminListView(StaffRequiredMixin, ListView):
  model = MaintenanceRequest
  template_name = 'dashboard/maintenance_admin_list.html'
  context_object_name = 'requests'
  paginate_by = 15

class MaintenanceRequestAdminUpdateView(StaffRequiredMixin, UpdateView):
  model = MaintenanceRequest
  form_class = MaintenanceRequestUpdateForm
  template_name = 'dashboard/maintenance_detail.html'
  success_url = reverse_lazy('maintenance_admin_list')

  def form_valid(self, form):
    messages.success(self.request, _('تم تحديث حالة طلب الصيانة بنجاح!'))
    return super().form_valid(form)

class DocumentUploadView(StaffRequiredMixin, CreateView):
  model = Document
  form_class = DocumentForm

  def form_valid(self, form):
    lease = get_object_or_404(Lease, pk=self.kwargs['lease_pk'])
    form.instance.lease = lease
    messages.success(self.request, _('تم رفع المستند بنجاح!'))
    return super().form_valid(form)

  def get_success_url(self):
    return reverse_lazy('lease_detail', kwargs={'pk': self.kwargs['lease_pk']})

class DocumentDeleteView(StaffRequiredMixin, DeleteView):
  model = Document
  template_name = 'dashboard/document_confirm_delete.html'

  def get_success_url(self):
    return reverse_lazy('lease_detail', kwargs={'pk': self.object.lease.pk})
    
  def form_valid(self, form):
    messages.success(self.request, _('تم حذف المستند بنجاح!'))
    return super().form_valid(form)

class ExpenseListView(StaffRequiredMixin, ListView):
  model = Expense
  template_name = 'dashboard/expense_list.html'
  context_object_name = 'expenses'
  paginate_by = 20

class ExpenseCreateView(StaffRequiredMixin, CreateView):
  model = Expense
  form_class = ExpenseForm
  template_name = 'dashboard/expense_form.html'
  success_url = reverse_lazy('expense_list')

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['title'] = _('إضافة مصروف جديد')
    return context

  def form_valid(self, form):
    messages.success(self.request, _('تم تسجيل المصروف بنجاح!'))
    return super().form_valid(form)

class ExpenseUpdateView(StaffRequiredMixin, UpdateView):
  model = Expense
  form_class = ExpenseForm
  template_name = 'dashboard/expense_form.html'
  success_url = reverse_lazy('expense_list')

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['title'] = _('تعديل المصروف')
    return context

  def form_valid(self, form):
    messages.success(self.request, _('تم تحديث المصروف بنجاح!'))
    return super().form_valid(form)

class ExpenseDeleteView(StaffRequiredMixin, DeleteView):
  model = Expense
  template_name = 'dashboard/expense_confirm_delete.html'
  success_url = reverse_lazy('expense_list')

  def form_valid(self, form):
    messages.success(self.request, _('تم حذف المصروف بنجاح!'))
    return super().form_valid(form)