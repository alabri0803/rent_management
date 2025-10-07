from django.shortcuts import render, get_object_or_404, redirect

def login_redirect(request):
    if request.user.is_staff:
        return redirect('dashboard_home')
    else:
        return redirect('portal_dashboard')
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.db import transaction
from dateutil.relativedelta import relativedelta
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from django.utils.translation import gettext as _
from django.conf import settings
from django import forms
import json

from .models import (
    Tenant, Unit, Building, Lease, Document, MaintenanceRequest, 
    Expense, Payment, Company, Invoice, InvoiceItem
)
from .forms import (
    TenantForm, UnitForm, BuildingForm, LeaseForm, DocumentForm, 
    MaintenanceRequestUpdateForm, ExpenseForm, PaymentForm, LeaseCancelForm, 
    CompanyForm, TenantRatingForm, InvoiceForm, InvoiceItemFormSet
)
from .utils import render_to_pdf

class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

# --- Dashboard Home ---
class DashboardHomeView(StaffRequiredMixin, ListView):
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
            month_name_en = date.strftime("%b")
            trend_chart['labels'].append(month_name_en)
            monthly_income = Payment.objects.filter(payment_date__year=date.year, payment_date__month=date.month).aggregate(total=Sum('amount'))['total'] or 0
            trend_chart['income_data'].append(float(monthly_income))
            monthly_expenses_trend = Expense.objects.filter(expense_date__year=date.year, expense_date__month=date.month).aggregate(total=Sum('amount'))['total'] or 0
            trend_chart['expense_data'].append(float(monthly_expenses_trend))
        context['trend_chart'] = trend_chart

        # Recent financial movements
        recent_payments = Payment.objects.order_by('-payment_date')[:5]
        recent_expenses = Expense.objects.order_by('-expense_date')[:5]
        context['recent_payments'] = recent_payments
        context['recent_expenses'] = recent_expenses # ADDED

        context['recent_requests'] = MaintenanceRequest.objects.order_by('-reported_date')[:5]

        total_units = Unit.objects.count()
        occupied_units = Unit.objects.filter(is_available=False).count()
        available_units = total_units - occupied_units
        context['occupancy_chart'] = {
            'labels': [_("مشغولة"), _("متاحة")],
            'data': [occupied_units, available_units],
        }

        # ADDED: Calendar data for renewals
        renewals = Lease.objects.filter(end_date__gte=today.date()).values('contract_number', 'end_date', 'tenant__name')
        calendar_events = []
        for renewal in renewals:
            calendar_events.append({
                'title': f"{_('تجديد عقد')} {renewal['contract_number']} - {renewal['tenant__name']}",
                'start': renewal['end_date'].isoformat(),
                'allDay': True,
            })
        context['calendar_events'] = json.dumps(calendar_events)

        # Alerts for expiring leases
        expiring_soon = Lease.objects.filter(
            status='expiring_soon',
            end_date__gte=today.date()
        ).order_by('end_date')[:5]
        context['expiring_leases'] = expiring_soon

        return context

# --- Units Management ---
class UnitListView(StaffRequiredMixin, ListView):
    model = Unit
    template_name = 'dashboard/unit_list.html'
    context_object_name = 'units'
    paginate_by = 20

    def get_queryset(self):
        queryset = Unit.objects.all().select_related('building').order_by('building', 'unit_number')
        search_query = self.request.GET.get('q', '')
        building_filter = self.request.GET.get('building', '')
        status_filter = self.request.GET.get('status', '')
        
        if search_query:
            queryset = queryset.filter(Q(unit_number__icontains=search_query) | Q(building__name__icontains=search_query))
        if building_filter:
            queryset = queryset.filter(building_id=building_filter)
        if status_filter == 'available':
            queryset = queryset.filter(is_available=True)
        elif status_filter == 'occupied':
            queryset = queryset.filter(is_available=False)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['buildings'] = Building.objects.all()
        context['total_units'] = Unit.objects.count()
        context['available_units'] = Unit.objects.filter(is_available=True).count()
        context['occupied_units'] = Unit.objects.filter(is_available=False).count()
        return context

class UnitDetailView(StaffRequiredMixin, DetailView):
    model = Unit
    template_name = 'dashboard/unit_detail.html'
    context_object_name = 'unit'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_lease'] = Lease.objects.filter(unit=self.object, status__in=['active', 'expiring_soon']).first()
        context['lease_history'] = Lease.objects.filter(unit=self.object).order_by('-start_date')
        return context

class UnitCreateView(StaffRequiredMixin, CreateView):
    model = Unit
    form_class = UnitForm
    template_name = 'dashboard/unit_form.html'
    success_url = reverse_lazy('unit_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("إضافة وحدة جديدة")
        return context

    def form_valid(self, form):
        messages.success(self.request, _("تمت إضافة الوحدة بنجاح!"))
        return super().form_valid(form)

class UnitUpdateView(StaffRequiredMixin, UpdateView):
    model = Unit
    form_class = UnitForm
    template_name = 'dashboard/unit_form.html'
    success_url = reverse_lazy('unit_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("تعديل الوحدة")
        return context

    def form_valid(self, form):
        messages.success(self.request, _("تم تحديث الوحدة بنجاح!"))
        return super().form_valid(form)

class UnitDeleteView(StaffRequiredMixin, DeleteView):
    model = Unit
    template_name = 'dashboard/unit_confirm_delete.html'
    success_url = reverse_lazy('unit_list')

    def form_valid(self, form):
        messages.success(self.request, _("تم حذف الوحدة بنجاح."))
        return super().form_valid(form)

# --- Tenants Management ---
class TenantListView(StaffRequiredMixin, ListView):
    model = Tenant
    template_name = 'dashboard/tenant_list.html'
    context_object_name = 'tenants'
    paginate_by = 20

    def get_queryset(self):
        queryset = Tenant.objects.all().order_by('name')
        search_query = self.request.GET.get('q', '')
        tenant_type = self.request.GET.get('type', '')
        
        if search_query:
            queryset = queryset.filter(Q(name__icontains=search_query) | Q(phone__icontains=search_query) | Q(email__icontains=search_query))
        if tenant_type:
            queryset = queryset.filter(tenant_type=tenant_type)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_tenants'] = Tenant.objects.count()
        context['individual_tenants'] = Tenant.objects.filter(tenant_type='individual').count()
        context['company_tenants'] = Tenant.objects.filter(tenant_type='company').count()
        return context

class TenantDetailView(StaffRequiredMixin, DetailView):
    model = Tenant
    template_name = 'dashboard/tenant_detail.html'
    context_object_name = 'tenant'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_leases'] = Lease.objects.filter(tenant=self.object, status__in=['active', 'expiring_soon'])
        context['lease_history'] = Lease.objects.filter(tenant=self.object).order_by('-start_date')
        context['total_payments'] = Payment.objects.filter(lease__tenant=self.object).aggregate(total=Sum('amount'))['total'] or 0
        return context

class TenantCreateView(StaffRequiredMixin, CreateView):
    model = Tenant
    form_class = TenantForm
    template_name = 'dashboard/tenant_form.html'
    success_url = reverse_lazy('tenant_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("إضافة مستأجر جديد")
        return context

    def form_valid(self, form):
        messages.success(self.request, _("تمت إضافة المستأجر بنجاح!"))
        return super().form_valid(form)

class TenantUpdateView(StaffRequiredMixin, UpdateView):
    model = Tenant
    form_class = TenantForm
    template_name = 'dashboard/tenant_form.html'
    success_url = reverse_lazy('tenant_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("تعديل بيانات المستأجر")
        return context

    def form_valid(self, form):
        messages.success(self.request, _("تم تحديث بيانات المستأجر بنجاح!"))
        return super().form_valid(form)

class TenantDeleteView(StaffRequiredMixin, DeleteView):
    model = Tenant
    template_name = 'dashboard/tenant_confirm_delete.html'
    success_url = reverse_lazy('tenant_list')

    def form_valid(self, form):
        messages.success(self.request, _("تم حذف المستأجر بنجاح."))
        return super().form_valid(form)

# --- Buildings Management ---
class BuildingListView(StaffRequiredMixin, ListView):
    model = Building
    template_name = 'dashboard/building_list.html'
    context_object_name = 'buildings'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for building in context['buildings']:
            building.total_units = building.unit_set.count()
            building.occupied_units = building.unit_set.filter(is_available=False).count()
            building.occupancy_rate = (building.occupied_units / building.total_units * 100) if building.total_units > 0 else 0
        return context

class BuildingCreateView(StaffRequiredMixin, CreateView):
    model = Building
    form_class = BuildingForm
    template_name = 'dashboard/building_form.html'
    success_url = reverse_lazy('building_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("إضافة مبنى جديد")
        return context

    def form_valid(self, form):
        messages.success(self.request, _("تمت إضافة المبنى بنجاح!"))
        return super().form_valid(form)

class BuildingUpdateView(StaffRequiredMixin, UpdateView):
    model = Building
    form_class = BuildingForm
    template_name = 'dashboard/building_form.html'
    success_url = reverse_lazy('building_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("تعديل المبنى")
        return context

    def form_valid(self, form):
        messages.success(self.request, _("تم تحديث المبنى بنجاح!"))
        return super().form_valid(form)

class BuildingDeleteView(StaffRequiredMixin, DeleteView):
    model = Building
    template_name = 'dashboard/building_confirm_delete.html'
    success_url = reverse_lazy('building_list')

    def form_valid(self, form):
        messages.success(self.request, _("تم حذف المبنى بنجاح."))
        return super().form_valid(form)

# --- Leases ---
class LeaseListView(StaffRequiredMixin, ListView):
    model = Lease
    template_name = 'dashboard/lease_list.html'
    context_object_name = 'leases'
    paginate_by = 10
    def get_queryset(self):
        queryset = Lease.objects.all().order_by('-start_date')
        search_query = self.request.GET.get('q', '')
        if search_query:
            queryset = queryset.filter(Q(contract_number__icontains=search_query) | Q(tenant__name__icontains=search_query) | Q(unit__unit_number__icontains=search_query))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # This loop is inefficient, status should be updated by a scheduled task
        # for lease in Lease.objects.all(): lease.save() 
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

class LeaseDetailView(StaffRequiredMixin, DetailView):
    model = Lease
    template_name = 'dashboard/lease_detail.html'
    context_object_name = 'lease'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['document_form'] = DocumentForm()
        context['payment_summary'] = self.object.get_payment_summary() # MODIFIED name
        context['total_paid'] = self.object.payments.aggregate(total=Sum('amount'))['total'] or 0
        context['rating_form'] = TenantRatingForm(instance=self.object.tenant) # ADDED
        return context

# ADDED: View to handle tenant rating update
class UpdateTenantRatingView(StaffRequiredMixin, View):
    def post(self, request, pk):
        tenant = get_object_or_404(Tenant, pk=pk)
        form = TenantRatingForm(request.POST, instance=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, _("تم تحديث تقييم العميل."))
        else:
            messages.error(request, _("حدث خطأ أثناء تحديث التقييم."))

        lease = Lease.objects.filter(tenant=tenant).first()
        return redirect('lease_detail', pk=lease.pk)

class LeaseCreateView(StaffRequiredMixin, CreateView):
    model = Lease; form_class = LeaseForm; template_name = 'dashboard/lease_form.html'; success_url = reverse_lazy('lease_list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs); context['title'] = _("إضافة عقد جديد"); return context
    def form_valid(self, form):
        messages.success(self.request, _("تمت إضافة العقد بنجاح!")); return super().form_valid(form)

class LeaseUpdateView(StaffRequiredMixin, UpdateView):
    model = Lease; form_class = LeaseForm; template_name = 'dashboard/lease_form.html'; success_url = reverse_lazy('lease_list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs); context['title'] = _("تعديل العقد"); return context
    def form_valid(self, form):
        messages.success(self.request, _("تم تحديث العقد بنجاح!")); return super().form_valid(form)

class LeaseDeleteView(StaffRequiredMixin, DeleteView):
    model = Lease; template_name = 'dashboard/lease_confirm_delete.html'; success_url = reverse_lazy('lease_list')
    def form_valid(self, form):
        messages.success(self.request, _("تم حذف العقد بنجاح.")); return super().form_valid(form)

# ADDED: Lease Cancellation View
class LeaseCancelView(StaffRequiredMixin, UpdateView):
    model = Lease
    form_class = LeaseCancelForm
    template_name = 'dashboard/lease_cancel_form.html'
    context_object_name = 'lease'

    def get_success_url(self):
        return reverse('lease_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        lease = form.save(commit=False)
        lease.status = 'cancelled'
        lease.cancellation_date = timezone.now().date()
        lease.unit.is_available = True
        lease.unit.save()
        lease.save()
        messages.success(self.request, _("تم إلغاء العقد بنجاح."))
        return super().form_valid(form)

# ... (renew_lease, Document views, Maintenance views, Expense views remain similar) ...

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
                messages.error(request, _("الرجاء إدخال تاريخ انتهاء صحيح.")); return redirect('lease_detail', pk=pk)

        # Create a new contract number to avoid unique constraint issues
        new_contract_number = f"{original_lease.contract_number}-R{Lease.objects.filter(contract_number__startswith=original_lease.contract_number).count()}"

        new_lease = Lease.objects.create(unit=original_lease.unit, tenant=original_lease.tenant, contract_number=new_contract_number, monthly_rent=original_lease.monthly_rent, start_date=new_start_date, end_date=new_end_date, electricity_meter=original_lease.electricity_meter, water_meter=original_lease.water_meter)
        original_lease.status = 'expired'; original_lease.save()
        messages.success(request, _("تم تجديد العقد بنجاح!")); return redirect('lease_detail', pk=new_lease.pk)
    return render(request, 'dashboard/lease_renew.html', {'lease': original_lease})

class DocumentUploadView(StaffRequiredMixin, CreateView):
    model = Document; form_class = DocumentForm
    def form_valid(self, form):
        lease = get_object_or_404(Lease, pk=self.kwargs.get('lease_pk')); form.instance.lease = lease
        messages.success(self.request, _("تم رفع المستند بنجاح!")); return super().form_valid(form)
    def get_success_url(self): return reverse('lease_detail', kwargs={'pk': self.kwargs.get('lease_pk')})

class DocumentDeleteView(StaffRequiredMixin, DeleteView):
    model = Document; template_name = 'dashboard/document_confirm_delete.html'
    def get_success_url(self): return reverse('lease_detail', kwargs={'pk': self.object.lease.pk})
    def form_valid(self, form):
        messages.success(self.request, _("تم حذف المستند بنجاح.")); return super().form_valid(form)

class MaintenanceRequestAdminListView(StaffRequiredMixin, ListView):
    model = MaintenanceRequest; template_name = 'dashboard/maintenance_list.html'; context_object_name = 'requests'; paginate_by = 15

class MaintenanceRequestAdminUpdateView(StaffRequiredMixin, UpdateView):
    model = MaintenanceRequest; form_class = MaintenanceRequestUpdateForm; template_name = 'dashboard/maintenance_detail.html'; success_url = reverse_lazy('maintenance_admin_list')
    def form_valid(self, form):
        messages.success(self.request, _("تم تحديث حالة طلب الصيانة بنجاح.")); return super().form_valid(form)

class ExpenseListView(StaffRequiredMixin, ListView):
    model = Expense; template_name = 'dashboard/expense_list.html'; context_object_name = 'expenses'; paginate_by = 20

class ExpenseCreateView(StaffRequiredMixin, CreateView):
    model = Expense; form_class = ExpenseForm; template_name = 'dashboard/expense_form.html'; success_url = reverse_lazy('expense_list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs); context['title'] = _("إضافة مصروف جديد"); return context
    def form_valid(self, form):
        messages.success(self.request, _("تم تسجيل المصروف بنجاح.")); return super().form_valid(form)

class ExpenseUpdateView(StaffRequiredMixin, UpdateView):
    model = Expense; form_class = ExpenseForm; template_name = 'dashboard/expense_form.html'; success_url = reverse_lazy('expense_list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs); context['title'] = _("تعديل المصروف"); return context
    def form_valid(self, form):
        messages.success(self.request, _("تم تحديث المصروف بنجاح.")); return super().form_valid(form)

class ExpenseDeleteView(StaffRequiredMixin, DeleteView):
    model = Expense; template_name = 'dashboard/expense_confirm_delete.html'; success_url = reverse_lazy('expense_list')
    def form_valid(self, form):
        messages.success(self.request, _("تم حذف المصروف بنجاح.")); return super().form_valid(form)


class PaymentListView(StaffRequiredMixin, ListView):
    model = Payment; template_name = 'dashboard/payment_list.html'; context_object_name = 'payments'; paginate_by = 20

class PaymentCreateView(StaffRequiredMixin, CreateView):
    model = Payment; form_class = PaymentForm; template_name = 'dashboard/payment_form.html'; success_url = reverse_lazy('payment_list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs); context['title'] = _("إضافة دفعة جديدة"); return context
    def form_valid(self, form):
        messages.success(self.request, _("تم تسجيل الدفعة بنجاح.")); return super().form_valid(form)

class PaymentUpdateView(StaffRequiredMixin, UpdateView):
    model = Payment; form_class = PaymentForm; template_name = 'dashboard/payment_form.html'; success_url = reverse_lazy('payment_list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs); context['title'] = _("تعديل الدفعة"); return context
    def form_valid(self, form):
        messages.success(self.request, _("تم تحديث الدفعة بنجاح.")); return super().form_valid(form)

# ADDED
class PaymentDeleteView(StaffRequiredMixin, DeleteView):
    model = Payment
    template_name = 'dashboard/payment_confirm_delete.html'
    success_url = reverse_lazy('payment_list')
    def form_valid(self, form):
        messages.success(self.request, _("تم حذف الدفعة بنجاح.")); return super().form_valid(form)

class PaymentReceiptPDFView(View):
    def get(self, request, pk):
        try:
            payment = Payment.objects.get(pk=pk)
            lease = payment.lease

            context = {
                'payment': payment,
                'lease': lease,
                'company': {
                    'name': 'شركة الإدارة العقارية',
                    'logo': None
                },
                'today': timezone.now().date(),
            }

            # استخدام الدالة المباشرة بدلاً من generate_pdf_receipt
            return self.render_pdf_receipt('dashboard/reports/payment_receipt.html', context)

        except Payment.DoesNotExist:
            return HttpResponse("Payment not found", status=404)

    def render_pdf_receipt(self, template_path, context):
        """دالة مساعدة لتوليد PDF"""
        try:
            # حاول استخدام WeasyPrint أولاً
            from weasyprint import HTML

            template = get_template(template_path)
            html = template.render(context)

            pdf_file = HTML(string=html, base_url=settings.BASE_DIR).write_pdf()

            response = HttpResponse(pdf_file, content_type='application/pdf')
            filename = f"receipt_{context['payment'].id}.pdf"
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            return response

        except ImportError:
            # إذا لم يكن WeasyPrint مثبتاً، استخدم xhtml2pdf
            return self.render_pdf_with_xhtml2pdf(template_path, context)
        except Exception as e:
            # في حالة الخطأ، ارجع HTML للتصحيح
            template = get_template(template_path)
            html = template.render(context)
            return HttpResponse(f"Error: {str(e)}<hr>{html}")

    def render_pdf_with_xhtml2pdf(self, template_path, context):
        """استخدام xhtml2pdf كبديل"""
        try:
            from xhtml2pdf import pisa

            template = get_template(template_path)
            html = template.render(context)

            result = BytesIO()
            pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

            if not pdf.err:
                response = HttpResponse(result.getvalue(), content_type='application/pdf')
                filename = f"receipt_{context['payment'].id}.pdf"
                response['Content-Disposition'] = f'inline; filename="{filename}"'
                return response
            else:
                return HttpResponse("PDF generation failed")

        except Exception as e:
            template = get_template(template_path)
            html = template.render(context)
            return HttpResponse(f"PDF Error: {str(e)}<hr>{html}")

# --- Check Management ---
class CheckManagementView(StaffRequiredMixin, ListView):
    model = Payment
    template_name = 'dashboard/check_management.html'
    context_object_name = 'checks'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Payment.objects.filter(payment_method='check').select_related('lease__tenant', 'lease__unit')
        
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(check_status=status_filter)
        
        return queryset.order_by('-payment_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        
        context['pending_count'] = Payment.objects.filter(payment_method='check', check_status='pending').count()
        context['cashed_count'] = Payment.objects.filter(payment_method='check', check_status='cashed').count()
        context['returned_count'] = Payment.objects.filter(payment_method='check', check_status='returned').count()
        context['total_count'] = Payment.objects.filter(payment_method='check').count()
        
        return context

class CheckStatusUpdateView(StaffRequiredMixin, UpdateView):
    model = Payment
    fields = ['check_status', 'return_reason']
    template_name = 'dashboard/check_status_form.html'
    success_url = reverse_lazy('check_management')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("تحديث حالة الشيك")
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _("تم تحديث حالة الشيك بنجاح."))
        return super().form_valid(form)

# --- User Management ---
class UserManagementForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False, label=_("كلمة المرور"))
    is_staff = forms.BooleanField(required=False, label=_("موظف"))
    is_active = forms.BooleanField(required=False, initial=True, label=_("نشط"))
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active']
        labels = {
            'username': _('اسم المستخدم'),
            'first_name': _('الاسم الأول'),
            'last_name': _('اسم العائلة'),
            'email': _('البريد الإلكتروني'),
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user

class UserManagementView(StaffRequiredMixin, ListView):
    model = User
    template_name = 'dashboard/user_management.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        return User.objects.all().order_by('-date_joined')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_users'] = User.objects.count()
        context['staff_users'] = User.objects.filter(is_staff=True).count()
        context['active_users'] = User.objects.filter(is_active=True).count()
        return context

class UserCreateView(StaffRequiredMixin, CreateView):
    model = User
    form_class = UserManagementForm
    template_name = 'dashboard/user_form.html'
    success_url = reverse_lazy('user_management')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("إضافة مستخدم جديد")
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _("تم إنشاء المستخدم بنجاح."))
        return super().form_valid(form)

class UserUpdateView(StaffRequiredMixin, UpdateView):
    model = User
    form_class = UserManagementForm
    template_name = 'dashboard/user_form.html'
    success_url = reverse_lazy('user_management')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("تعديل المستخدم")
        return context
    
    def form_valid(self, form):
        messages.success(self.request, _("تم تحديث المستخدم بنجاح."))
        return super().form_valid(form)

class UserDeleteView(StaffRequiredMixin, DeleteView):
    model = User
    template_name = 'dashboard/user_confirm_delete.html'
    success_url = reverse_lazy('user_management')
    
    def form_valid(self, form):
        messages.success(self.request, _("تم حذف المستخدم بنجاح."))
        return super().form_valid(form)

# --- Reports ---
# --- Invoice Views ---
class InvoiceListView(StaffRequiredMixin, ListView):
    model = Invoice
    template_name = 'dashboard/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20

    def get_queryset(self):
        queryset = Invoice.objects.select_related('tenant', 'lease').all()
        search_query = self.request.GET.get('q', '')
        if search_query:
            queryset = queryset.filter(
                Q(invoice_number__icontains=search_query) |
                Q(tenant__name__icontains=search_query) |
                Q(lease__contract_number__icontains=search_query)
            )
        return queryset.order_by('-issue_date')

class InvoiceDetailView(StaffRequiredMixin, DetailView):
    model = Invoice
    template_name = 'dashboard/invoice_detail.html'
    context_object_name = 'invoice'

class InvoiceCreateView(StaffRequiredMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'dashboard/invoice_form.html'
    success_url = reverse_lazy('invoice_list')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['items'] = InvoiceItemFormSet(self.request.POST)
        else:
            data['items'] = InvoiceItemFormSet()
        data['title'] = _("إنشاء فاتورة جديدة")
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        items = context['items']
        with transaction.atomic():
            self.object = form.save()
            if items.is_valid():
                items.instance = self.object
                items.save()
                messages.success(self.request, _("تم إنشاء الفاتورة بنجاح."))
            else:
                # If items are not valid, we prevent the form from being considered valid.
                return self.form_invalid(form)
        return super().form_valid(form)

class InvoiceUpdateView(StaffRequiredMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'dashboard/invoice_form.html'

    def get_success_url(self):
        return reverse('invoice_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['items'] = InvoiceItemFormSet(self.request.POST, instance=self.object)
        else:
            data['items'] = InvoiceItemFormSet(instance=self.object)
        data['title'] = _("تعديل الفاتورة")
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        items = context['items']
        with transaction.atomic():
            self.object = form.save()
            if items.is_valid():
                items.instance = self.object
                items.save()
                messages.success(self.request, _("تم تحديث الفاتورة بنجاح."))
            else:
                return self.form_invalid(form)
        return super().form_valid(form)

class InvoiceDeleteView(StaffRequiredMixin, DeleteView):
    model = Invoice
    template_name = 'dashboard/invoice_confirm_delete.html'
    success_url = reverse_lazy('invoice_list')

    def form_valid(self, form):
        messages.success(self.request, _("تم حذف الفاتورة بنجاح."))
        return super().form_valid(form)

# --- Reports ---
class ReportSelectionView(StaffRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return render(request, 'dashboard/report_selection.html')

class GenerateTenantStatementPDF(StaffRequiredMixin, View):
    def get(self, request, lease_pk, *args, **kwargs):
        lease = get_object_or_404(Lease, pk=lease_pk)
        context = {
            'lease': lease, 
            'payments': lease.payments.all(), 
            'today': timezone.now(),
            'company': Company.objects.first() # ADDED
        }
        return render_to_pdf('dashboard/reports/tenant_statement.html', context)

# ADDED
class GeneratePaymentReceiptPDF(StaffRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        payment = get_object_or_404(Payment, pk=pk)
        context = {
            'payment': payment,
            'lease': payment.lease,
            'company': Company.objects.first()
        }
        return render_to_pdf('dashboard/reports/payment_receipt.html', context)

class GenerateMonthlyPLReportPDF(StaffRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        year = request.GET.get('year'); month = request.GET.get('month')
        if not year or not month:
            messages.error(request, _("الرجاء تحديد السنة والشهر.")); return redirect('report_selection')
        year, month = int(year), int(month)
        income = Payment.objects.filter(payment_date__year=year, payment_date__month=month)
        expenses = Expense.objects.filter(expense_date__year=year, expense_date__month=month)
        total_income = income.aggregate(total=Sum('amount'))['total'] or 0
        total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
        context = {
            'income_list': income, 'expenses_list': expenses, 'total_income': total_income,
            'total_expenses': total_expenses, 'net_profit': total_income - total_expenses,
            'report_month': month, 'report_year': year, 'company': Company.objects.first() # ADDED
        }
        return render_to_pdf('dashboard/reports/monthly_pl_report.html', context)

# ADDED
class GenerateAnnualPLReportPDF(StaffRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        year = request.GET.get('year')
        if not year:
            messages.error(request, _("الرجاء تحديد السنة.")); return redirect('report_selection')
        year = int(year)
        income = Payment.objects.filter(payment_date__year=year)
        expenses = Expense.objects.filter(expense_date__year=year)
        total_income = income.aggregate(total=Sum('amount'))['total'] or 0
        total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
        context = {
            'income_list': income, 'expenses_list': expenses, 'total_income': total_income,
            'total_expenses': total_expenses, 'net_profit': total_income - total_expenses,
            'report_year': year, 'company': Company.objects.first()
        }
        return render_to_pdf('dashboard/reports/annual_pl_report.html', context)

# ADDED
class GenerateOccupancyReportPDF(StaffRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        buildings = Building.objects.all().prefetch_related('unit_set')
        total_units = Unit.objects.count()
        occupied_units = Unit.objects.filter(is_available=False).count()
        occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0
        context = {
            'buildings': buildings,
            'total_units': total_units,
            'occupied_units': occupied_units,
            'available_units': total_units - occupied_units,
            'occupancy_rate': occupancy_rate,
            'today': timezone.now().date(),
            'company': Company.objects.first()
        }
        return render_to_pdf('dashboard/reports/occupancy_report.html', context)

# --- Settings ---
# ADDED
class CompanyUpdateView(StaffRequiredMixin, UpdateView):
    model = Company
    form_class = CompanyForm
    template_name = 'dashboard/company_form.html'
    success_url = reverse_lazy('company_update')

    def get_object(self):
        # Get or create the first company profile
        obj, created = Company.objects.get_or_create(pk=1)
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("إعدادات الشركة والهوية")
        return context

    def form_valid(self, form):
        messages.success(self.request, _("تم تحديث بيانات الشركة بنجاح."))
        return super().form_valid(form)