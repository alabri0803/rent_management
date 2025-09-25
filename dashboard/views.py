from django import template
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Sum, Count, Q
from dateutil.relativedelta import relativedelta
from django.template import Context, Template
from num2words import num2words

from .models import Lease, Unit, Payment, MaintenanceRequest, Document, Expense, Tenant
from .forms import LeaseForm, DocumentForm, MaintenanceRequestUpdateForm, PaymentForm, ExpenseForm, SendMessageForm, LeaseCancellationForm
from .utils import render_to_pdf

# Mixin for Staff Users
class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

# --- Dashboard Home ---
class DashboardHomeView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'dashboard.view_lease'
    model = Lease
    template_name = 'dashboard/home.html'
    context_object_name = 'leases'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now()

        # Stats Cards
        active_leases = Lease.objects.filter(status__in=['active', 'expiring_soon'])
        monthly_expenses = Expense.objects.filter(expense_date__year=today.year, expense_date__month=today.month).aggregate(total=Sum('amount'))['total'] or 0
        expected_income = active_leases.aggregate(total=Sum('monthly_rent'))['total'] or 0

        context['stats'] = {
            'active_count': active_leases.count(),
            'expected_monthly_income': expected_income,
            'monthly_expenses': monthly_expenses,
            'net_income': expected_income - monthly_expenses
        }

        # Financial Trend Chart (Last 12 months)
        trend_chart = {'labels': [], 'income_data': [], 'expense_data': []}
        for i in range(12, 0, -1):
            date = today - relativedelta(months=i-1)
            month_name_en = date.strftime("%b") # English month name for consistency in JS
            trend_chart['labels'].append(month_name_en)

            monthly_income = Payment.objects.filter(payment_date__year=date.year, payment_date__month=date.month).aggregate(total=Sum('amount'))['total'] or 0
            trend_chart['income_data'].append(float(monthly_income))

            monthly_expenses_trend = Expense.objects.filter(expense_date__year=date.year, expense_date__month=date.month).aggregate(total=Sum('amount'))['total'] or 0
            trend_chart['expense_data'].append(float(monthly_expenses_trend))
        context['trend_chart'] = trend_chart
        context['recent_payments'] = Payment.objects.order_by('-payment_date')[:5]
        context['recent_requests'] = MaintenanceRequest.objects.order_by('-reported_date')[:5]
        total_units = Unit.objects.count()
        occupied_units = Unit.objects.filter(is_available=False).count()
        available_units = total_units - occupied_units
        context['occupancy_chart'] = {
            'labels': [_("متاح"), _("مستأجر")],
            'data': [occupied_units, available_units],
        }
        return context


class LeaseListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'dashboard.view_lease'
    model = Lease
    template_name = 'dashboard/lease_list.html'
    context_object_name = 'leases'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Lease.objects.all().order_by('-start_date')
        search_query = self.request.GET.get('q', '')
        if search_query:
            queryset = queryset.filter(Q(tenant__name__icontains=search_query) | Q(contract_number__icontains=search_query) | Q(unit__unit_number__icontains=search_query))
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for lease in Lease.objects.all(): lease.save()
        active_leases = Lease.objects.filter(status='active')
        today = timezone.now()
        monthly_expenses = Expense.objects.filter(expense_date__year=today.year, expense_date__month=today.month).aggregate(total=Sum('amount'))['total'] or 0
        gross_income = active_leases.aggregate(total=Sum('monthly_rent'))['total'] or 0
        context['stats'] = {
            'active_count': active_leases.count(),
            'expiring_count': Lease.objects.filter(status='expiring_soon').count(),
            'expired_count': Lease.objects.filter(status='expired').count(),
            'total_units': Unit.objects.count(),
            'available_units': Unit.objects.filter(is_available=True).count(),
            'expected_monthly_income': gross_income,
            'monthly_expenses': monthly_expenses,
            'net_income': gross_income - monthly_expenses
        }
        status_counts = Lease.objects.values('status').annotate(count=Count('status'))
        chart_data = {'labels': [], 'data': []}
        status_display_map = dict(Lease.STATUS_CHOICES)
        for item in status_counts:
            chart_data['labels'].append(str(status_display_map.get(item['status'], item['status'])))
            chart_data['data'].append(item['count'])
        context['chart_data'] = chart_data
        return context

class LeaseDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    permission_required = 'dashboard.view_lease'
    model = Lease
    template_name = 'dashboard/lease_detail.html'
    context_object_name = 'lease'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['document_form'] = DocumentForm()
        context['paymnt_summary'] = self.object.get_payment_summary()
        context['total_paid'] = self.object.payments.aggregate(total=Sum('amount'))['total'] or 0
        return context

class LeaseCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'dashboard.add_lease'
    model = Lease
    form_class = LeaseForm
    template_name = 'dashboard/lease_form.html'
    success_url = reverse_lazy('lease_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("إضافة عقد جديد")
        return context
        
    def form_valid(self, form):
        messages.success(self.request, _("تمت إضافة العقد بنجاح!"))
        return super().form_valid(form)

class LeaseUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'dashboard.change_lease'
    model = Lease
    form_class = LeaseForm
    template_name = 'dashboard/lease_form.html'
    success_url = reverse_lazy('lease_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("تعديل العقد")
        return context
        
    def form_valid(self, form):
        messages.success(self.request, _("تم تحديث العقد بنجاح!"))
        return super().form_valid(form)

class LeaseDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = 'dashboard.delete_lease'
    model = Lease
    template_name = 'dashboard/lease_confirm_delete.html'
    success_url = reverse_lazy('lease_list')
    
    def form_valid(self, form):
        messages.success(self.request, _("تم حذف العقد بنجاح."))
        return super().form_valid(form)

@login_required
@user_passes_test(lambda u: u.is_staff)
def renew_lease(request, pk):
    original_lease = get_object_or_404(Lease, pk=pk)
    if request.method == 'POST':
        duration = request.POST.get('duration')
        new_start_date = original_lease.end_date + relativedelta(days=1)
        if duration == '1y': new_end_date = new_start_date + relativedelta(years=1, days=-1)
        elif duration == '6m': new_end_date = new_start_date + relativedelta(months=6, days=-1)
        elif duration == '3m': new_end_date = new_start_date + relativedelta(months=3, days=-1)
        else:
            new_end_date = request.POST.get('manual_date')
            if not new_end_date:
                messages.error(request, _("الرجاء إدخال تاريخ انتهاء صحيح."))
                return redirect('lease_detail', pk=pk)
        new_lease = Lease.objects.create(unit=original_lease.unit, tenant=original_lease.tenant, contract_number=f"{original_lease.contract_number}-R", monthly_rent=original_lease.monthly_rent, start_date=new_start_date, end_date=new_end_date, electricity_meter=original_lease.electricity_meter, water_meter=original_lease.water_meter)
        original_lease.status = 'expired'; original_lease.save()
        messages.success(request, _("تم تجديد العقد بنجاح!"))
        return redirect('lease_detail', pk=new_lease.pk)
    return render(request, 'dashboard/lease_renew.html', {'lease': original_lease})

class DocumentUploadView(StaffRequiredMixin, CreateView):
    model = Document
    form_class = DocumentForm
    def form_valid(self, form):
        lease = get_object_or_404(Lease, pk=self.kwargs.get('lease_pk'))
        form.instance.lease = lease
        messages.success(self.request, _("تم رفع المستند بنجاح!"))
        return super().form_valid(form)
    def get_success_url(self): return reverse('lease_detail', kwargs={'pk': self.kwargs.get('lease_pk')})

class DocumentDeleteView(StaffRequiredMixin, DeleteView):
    model = Document
    template_name = 'dashboard/document_confirm_delete.html'
    
    def get_success_url(self): 
        return reverse('lease_detail', kwargs={'pk': self.object.lease.pk})
        
    def form_valid(self, form):
        messages.success(self.request, _("تم حذف المستند بنجاح."))
        return super().form_valid(form)

class MaintenanceRequestAdminListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'dashboard.view_maintenancerequest'
    model = MaintenanceRequest
    template_name = 'dashboard/maintenance_list.html'
    context_object_name = 'requests'
    paginate_by = 15

class MaintenanceRequestAdminUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'dashboard.change_maintenancerequest'
    model = MaintenanceRequest
    form_class = MaintenanceRequestUpdateForm
    template_name = 'dashboard/maintenance_detail.html'
    success_url = reverse_lazy('maintenance_admin_list')
    
    def form_valid(self, form):
        messages.success(self.request, _("تم تحديث حالة طلب الصيانة بنجاح."))
        return super().form_valid(form)

class ExpenseListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'dashboard.view_expense'
    model = Expense
    template_name = 'dashboard/expense_list.html'
    context_object_name = 'expenses'
    paginate_by = 20

class ExpenseCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'dashboard.add_expense'
    model = Expense
    form_class = ExpenseForm
    template_name = 'dashboard/expense_form.html'
    success_url = reverse_lazy('expense_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("إضافة مصروف جديد")
        return context
        
    def form_valid(self, form):
        messages.success(self.request, _("تم تسجيل المصروف بنجاح."))
        return super().form_valid(form)

class ExpenseUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'dashboard.change_expense'
    model = Expense
    form_class = ExpenseForm
    template_name = 'dashboard/expense_form.html'
    success_url = reverse_lazy('expense_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("تعديل المصروف")
        return context
        
    def form_valid(self, form):
        messages.success(self.request, _("تم تحديث المصروف بنجاح."))
        return super().form_valid(form)

class ExpenseDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = 'dashboard.delete_expense'
    model = Expense
    template_name = 'dashboard/expense_confirm_delete.html'
    success_url = reverse_lazy('expense_list')
    
    def form_valid(self, form):
        messages.success(self.request, _("تم حذف المصروف بنجاح."))
        return super().form_valid(form)

class ReportSelectionView(StaffRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return render(request, 'dashboard/report_selection.html')

class GenerateTenantStatementPDF(StaffRequiredMixin, View):
    def get(self, request, lease_pk, *args, **kwargs):
        lease = get_object_or_404(Lease, pk=lease_pk)
        context = {'lease': lease, 'payments': lease.payments.all(), 'today': timezone.now()}
        return render_to_pdf('dashboard/reports/tenant_statement.html', context)

class GenerateMonthlyPLReportPDF(StaffRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        year = request.GET.get('year'); month = request.GET.get('month')
        if not year or not month:
            messages.error(request, _("الرجاء تحديد السنة والشهر."))
            return redirect('report_selection')
        year, month = int(year), int(month)
        income = Payment.objects.filter(payment_date__year=year, payment_date__month=month)
        expenses = Expense.objects.filter(expense_date__year=year, expense_date__month=month)
        total_income = income.aggregate(total=Sum('amount'))['total'] or 0
        total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
        context = {
            'income_list': income, 'expenses_list': expenses,
            'total_income': total_income, 'total_expenses': total_expenses,
            'net_profit': total_income - total_expenses,
            'report_month': month, 'report_year': year,
        }
        return render_to_pdf('dashboard/reports/monthly_pl_report.html', context)

class PaymentListView(StaffRequiredMixin, ListView):
    model = Payment
    template_name = 'dashboard/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 20

class PaymentCreateView(StaffRequiredMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'dashboard/payment_form.html'
    success_url = reverse_lazy('payment_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("إضافة دفعة جديدة")
        return context
        
    def form_valid(self, form):
        messages.success(self.request, _("تم تسجيل الدفعة بنجاح."))
        return super().form_valid(form)

class PaymentUpdateView(StaffRequiredMixin, UpdateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'dashboard/payment_form.html'
    success_url = reverse_lazy('payment_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("تعديل الدفعة")
        return context
        
    def form_valid(self, form):
        messages.success(self.request, _("تم تحديث الدفعة بنجاح."))
        return super().form_valid(form)

class TenantListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'dashboard.view_tenant'
    model = Tenant
    template_name = 'dashboard/tenant_list.html'
    context_object_name = 'tenants'
    paginate_by = 15

    def get_queryset(self):
        queryset = Tenant.objects.all().order_by('name')
        search_query = self.request.GET.get('q', '')
        if search_query:
            queryset = queryset.filter(Q(name__icontains=search_query) | Q(phone__icontains=search_query) | Q(email__icontains=search_query))
        return queryset

class TenantDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    permission_required = 'dashboard.view_tenant'
    model = Tenant
    template_name = 'dashboard/tenant_detail.html'
    context_object_name = 'tenant'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.object
        context['message_form'] = SendMessageForm()
        context['all_leases'] = Lease.objects.filter(tenant=tenant).order_by('-start_date')
        context['all_payments'] = Payment.objects.filter(lease__tenant=tenant).order_by('-payment_date')
        context['all_maintenance'] = MaintenanceRequest.objects.filter(lease__tenant=tenant).order_by('-reported_date')
        return context

    def post(self, request, *args, **kwargs):
        if 'update_tenant' in request.POST:
            return super().post(request, *args, **kwargs)
        elif 'send_message' in request.POST:
            tenant = self.get_object()
            form = SendMessageForm(request.POST)
            if form.is_valid() and tenant.user:
                notification = form.save(commit=False)
                notification.user = tenant.user
                notification.sent_by = request.user
                notification.save()
                messages.success(request, _("تم إرسال الرسالة بنجاح."))
            else:
                messages.error(request, _("لا يمكن ارسال الرسالة قد لا يكون للمستاجر حساب مرتبط."))
            return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('tenant_detail', kwargs={'pk': self.object.pk})

class CancelLeaseView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'dashboard.canc_cancel_lease'
    model = Lease
    form_class = LeaseCancellationForm
    template_name = 'dashboard/lease_cancel_form.html'

    def from_valid(self, form):
        lease = self.get_object()
        lease.status = 'cancelled'
        lease.unit.is_available = True
        lease.unit.save()
        messages.success(self.request, _("تم إلغاء العقد بنجاح."))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('lease_detail', kwargs={'pk': self.object.pk})

class GenerateContractPDF(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'dashboard.view_lease'

    def get(self, request, pk):
        lease = get_object_or_404(Lease, pk=pk)
        if not lease.template:
            messages.error(request, _("هذا العقد غير مرتبط بأي قالب."))
            return redirect('lease_detail', pk=pk)

        template_str = lease.template.body
        template = Template(template_str)

        # تحضير context للتعويض في القالب
        context_data = {
            'tenant_name': lease.tenant.name,
            'unit_full_address': f"{lease.unit.unit_number}, {lease.unit.building.name}, {lease.unit.building.address}",
            'start_date': lease.start_date.strftime('%d/%m/%Y'),
            'end_date': lease.end_date.strftime('%d/%m/%Y'),
            'monthly_rent_amount': f"{lease.monthly_rent:,.2f}",
            'monthly_rent_words': num2words(lease.monthly_rent, lang='ar'), # يتطلب تثبيت pip install num2words
            'contract_number': lease.contract_number,
        }
        context = Context(context_data)
        html_content = template.render(context)

        # استخدام دالة render_to_pdf الموجودة مسبقًا
        # ملاحظة: يجب تعديل دالة render_to_pdf لتستخدم خط يدعم العربية
        pdf_context = {'content': html_content}
        return render_to_pdf('dashboard/reports/contract_template.html', pdf_context)