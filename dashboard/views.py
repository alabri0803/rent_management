from itertools import chain
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Sum, Count, Q, Avg, F, Value
from django.db.models.functions import Coalesce
from django.core.serializers.json import DjangoJSONEncoder
import json
from operator import attrgetter
from dateutil.relativedelta import relativedelta
from django.template import Context, Template
from num2words import num2words
from datetime import datetime
from django.views.generic import TemplateView

from .models import Lease, Unit, Payment, MaintenanceRequest, Document, Expense, Tenant, Building, Notification
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
        current_month = today.month
        current_year = today.year

        # Stats Cards
        active_leases = Lease.objects.filter(status__in=['active', 'expiring_soon'])
        total_overdue = 0
        for lease in active_leases:
            summary = lease.get_payment_summary()
            for month_summary in summary:
                is_past_due = (month_summary['year'] < current_year) or (month_summary['year'] == current_year and month_summary['month'] < current_month)
                if is_past_due and month_summary['status'] in ['due', 'partial']:
                    total_overdue += month_summary['balance']

        context['stats'] = {
            'active_leases_count': active_leases.count(),
            'monthly_expected_income': active_leases.aggregate(total=Sum('monthly_rent'))['total'] or 0,
            'expiring_this_month': Lease.objects.filter(status='expiring_soon', end_date__month=current_month, end_date__year=current_year).count(),
            'vacant_units_count': Unit.objects.filter(is_available=True).count(),
            'total_overdue_rent': total_overdue,
            'maintenance_requests_open': MaintenanceRequest.objects.filter(status__in=['submitted', 'in_progress']).count(),
        }
        lease_events = []
        leases_for_calendar = Lease.objects.filter(status__in=['active', 'expiring_soon'])
        for lease in leases_for_calendar:
            lease_events.append({
                'title': _("انتهاء عقد")+ f" ({lease.unit.unit_number})",
                'start': lease.end_date,
                'url': lease.get_absolute_url(),
                'color': '#ef4444' if lease.status == 'expiring_soon' else '#3b82f6',
            })
            context['lease_events_json'] = json.dumps(lease_events, cls=DjangoJSONEncoder)
            context['notifications'] = Notification.objects.filter(user=self.request.user, read=False).order_by('-timestamp')[:5]
            latest_payments = Payment.objects.all().order_by('-payment_date')[:5]
            latest_expenses = Expense.objects.all().order_by('-expense_date')[:5]
            for p in latest_payments: p.type = 'income'; p.date = p.payment_date
            for e in latest_expenses: e.type = 'expense'; e.date = e.expense_date

        # Financial Trend Chart (Last 12 months)
        financial_feed = sorted(
            chain(latest_payments, latest_expenses), 
            key=attrgetter('date'), 
            reverse=True
        )
        context['financial_feed'] = financial_feed[:7]
        context['occupancy_chart_data'] = {
            'occupied': Unit.objects.filter(is_available=False).count(),
            'available': Unit.objects.filter(is_available=True).count(),
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

class ReportSelectionView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'dashboard.view_lease'
    def get(self, request, *args, **kwargs):
        context = {
            'buildings': Building.objects.all(),
        }
        return render(request, 'dashboard/report_selection.html', context)

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
                messages.error(request, _("هذا العقد غير مرتبط باي قالب"))
            return redirect('lease_detail', pk=kwargs['pk'])

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

class GenerateReceiptVoucherPDF(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'dashboard.view_payment'
    def get(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk)
        context = {
            'payment': payment,
            'amount_in_words': num2words(payment.amount, lang='ar'),
        }
        return render_to_pdf('dashboard/reports/receipt_voucher.html', context)

class GeneratePaymentVoucherPDF(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'dashboard.view_expense'
    def get(self, request, pk):
        expense = get_object_or_404(Expense, pk=pk)
        context = {
            'expense': expense,
            'amount_in_words': num2words(expense.amount, lang='ar'),
        }
        return render_to_pdf('dashboard/reports/payment_voucher.html', context)

class GenerateBuildingStatementPDF(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'dashboard.view_buildings_reports'
    def get(self, request, *args, **kwargs):
        building_id = request.GET.get('building')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if not all([building_id, start_date, end_date]):
            messages.error(request, _("الرجاء تحديد المبنى وتاريخ البدء والانتهاء."))
            return redirect('report_selection')
        building = get_object_or_404(Building, pk=building_id)
        income = Payment.objects.filter(lease__unit__building=building, payment_date__range=[start_date, end_date]).order_by('payment_date')
        expenses = Expense.objects.filter(building=building, expense_date__range=[start_date, end_date]).order_by('expense_date')
        total_income = income.aggregate(total=Sum('amount'))['total'] or 0
        total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
        context = {
            'building': building,
            'start_date': start_date,
            'end_date': end_date,
            'income_list': income,
            'expenses_list': expenses,
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_profit': total_income - total_expenses,
        }
        return render_to_pdf('dashboard/reports/building_statement.html', context)

class AnalyticsHubView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = 'dashboard.view_lease' # Or a general reporting permission
    template_name = 'dashboard/analytics_hub.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        current_year = today.year

        # --- 1. إحصائيات رئيسية ---
        total_income_ytd = Payment.objects.filter(payment_date__year=current_year).aggregate(Sum('amount'))['amount__sum'] or 0
        total_expenses_ytd = Expense.objects.filter(expense_date__year=current_year).aggregate(Sum('amount'))['amount__sum'] or 0
        context['kpis'] = {
            'total_income_ytd': total_income_ytd,
            'total_expenses_ytd': total_expenses_ytd,
            'net_profit_ytd': total_income_ytd - total_expenses_ytd,
            'occupancy_rate': (Unit.objects.filter(is_available=False).count() / Unit.objects.count() * 100) if Unit.objects.count() > 0 else 0
        }

        # --- 2. بيانات الرسم البياني: الإيرادات والمصروفات الشهرية (آخر 12 شهر) ---
        chart_data = {'labels': [], 'income': [], 'expenses': []}
        for i in range(11, -1, -1):
            month_date = today - relativedelta(months=i)
            chart_data['labels'].append(month_date.strftime('%b %Y'))
            income = Payment.objects.filter(payment_date__year=month_date.year, payment_date__month=month_date.month).aggregate(Sum('amount'))['amount__sum'] or 0
            expenses = Expense.objects.filter(expense_date__year=month_date.year, expense_date__month=month_date.month).aggregate(Sum('amount'))['amount__sum'] or 0
            chart_data['income'].append(float(income))
            chart_data['expenses'].append(float(expenses))
        context['monthly_trend_chart'] = chart_data

        # --- 3. بيانات الرسم البياني: المصروفات حسب الفئة (هذا العام) ---
        expense_breakdown = Expense.objects.filter(expense_date__year=current_year).values('category').annotate(total=Sum('amount')).order_by('-total')
        context['expense_chart'] = {
            'labels': [item['get_category_display'] for item in Expense.objects.filter(pk__in=[e['pk'] for e in expense_breakdown])] if expense_breakdown else [],
             'data': [float(item['total']) for item in expense_breakdown]
        }

        # --- 4. بيانات الرسم البياني: ربحية العقارات (هذا العام) ---
        properties_profit = Building.objects.annotate(
            income=Sum('unit__lease__payments__amount', filter=Q(unit__lease__payments__payment_date__year=current_year)),
            costs=Sum('expenses__amount', filter=Q(expenses__expense_date__year=current_year))
        ).annotate(
            net=F('income') - F('costs')
        ).order_by('-net')

        context['profit_chart'] = {
            'labels': [p.name for p in properties_profit],
            'data': [float(p.net or 0) for p in properties_profit]
        }

        context['available_years'] = range(2023, today.year + 1)
        return context

class GenerateAnnualReportPDF(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        year = request.GET.get('year')
        monthly_data = []
        for month in range(1, 13):
            income = Payment.objects.filter(payment_date__year=year, payment_date__month=month).aggregate(total=Sum('amount'))['amount__sum'] or 0
            expenses = Expense.objects.filter(expense_date__year=year, expense_date__month=month).aggregate(total=Sum('amount'))['amount__sum'] or 0
            monthly_data.append({
                'month': month,
                'income': income,
                'expenses': expenses,
                'net': income - expenses,
            })
            totals = {
                'total_income': sum(m['income'] for m in monthly_data),
                'total_expenses': sum(m['expenses'] for m in monthly_data),
                'total_net': sum(m['net'] for m in monthly_data),
            }
            context = {
                'year': year,
                'monthly_data': monthly_data,
                'totals': totals,
            }
            return render_to_pdf('dashboard/reports/annual_report.html', context)

class OccupancyReportView(LoginRequiredMixin, ListView):
    model = Building
    template_name = 'dashboard/occupancy_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['available_units'] = Unit.objects.filter(is_available=True).order_by('building', 'unit_number')
        context['today'] = timezone.now().date()

class TopClientsReportView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/top_clients_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['top_by_rating'] = Tenant.objects.all().order_by('-rating', 'name')[:10]
        context['top_by_value'] = Tenant.objects.annotate(total_paid=Sum('lease__payments__amount')).filter(total_paid__isnull=False).order_by('-total_paid', 'name')[:10]
        return context

class TopPropertiesReportView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/top_properties_report.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_year = timezone.now().year
        context['top_by_profit'] = Building.objects.annotate(
            income=Sum('unit__lease__payments__amount', filter=Q(unit__lease__payments__payment_date__year=current_year)),
            costs=Sum('expenses__amount', filter=Q(expenses__expense_date__year=current_year))
        ).annotate(
            net_profit=F('income') - F('costs')
        ).filter(net_profit__isnull=False).order_by('-net_profit')
        return context