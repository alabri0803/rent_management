from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.translation import gettext as _
from django.db.models import Sum, Count
from decimal import Decimal
from .models import Tenant, Lease, Payment, Expense, Building, Unit, MaintenanceRequest
from .excel_utils import ExcelExporter


def staff_required(user):
    """فقط الموظفين يمكنهم تصدير البيانات"""
    return user.is_staff


@login_required
@user_passes_test(staff_required)
def export_tenants_excel(request):
    """تصدير قائمة المستأجرين إلى Excel"""
    exporter = ExcelExporter("قائمة المستأجرين")
    
    # العناوين
    headers = ["#", "الاسم", "النوع", "رقم الهاتف", "البريد الإلكتروني", "المفوض بالتوقيع", "التقييم"]
    
    # العنوان
    exporter.add_title("قائمة المستأجرين", num_columns=len(headers))
    exporter.add_empty_row()
    
    exporter.create_header(headers)
    
    # البيانات
    tenants = Tenant.objects.all().order_by('name')
    total_count = tenants.count()
    
    for idx, tenant in enumerate(tenants, 1):
        tenant_type_display = "فرد" if tenant.tenant_type == 'individual' else "شركة"
        exporter.add_row([
            idx,
            tenant.name,
            tenant_type_display,
            tenant.phone,
            tenant.email or "-",
            tenant.authorized_signatory or "-",
            f"{'⭐' * tenant.rating} ({tenant.rating}/5)"
        ])
    
    # المجموع
    exporter.add_empty_row()
    exporter.add_total_row("إجمالي المستأجرين", total_count, col_span=len(headers))
    
    # عرض الأعمدة
    exporter.set_column_widths([8, 25, 15, 18, 30, 25, 18])
    
    return exporter.get_response("قائمة_المستأجرين.xlsx")


@login_required
@user_passes_test(staff_required)
def export_leases_excel(request):
    """تصدير قائمة العقود إلى Excel"""
    exporter = ExcelExporter("قائمة العقود")
    
    # العناوين
    headers = ["#", "رقم العقد", "المستأجر", "الوحدة", "الإيجار الشهري", "تاريخ البدء", "تاريخ الانتهاء", "الحالة"]
    
    # العنوان
    exporter.add_title("قائمة العقود", num_columns=len(headers))
    exporter.add_empty_row()
    
    exporter.create_header(headers)
    
    # البيانات
    leases = Lease.objects.all().select_related('tenant', 'unit', 'unit__building').order_by('-start_date')
    total_leases = leases.count()
    total_monthly_rent = Decimal('0')
    active_leases = 0
    
    for idx, lease in enumerate(leases, 1):
        status_display = {
            'active': 'نشط',
            'expiring_soon': 'ينتهي قريباً',
            'expired': 'منتهي',
            'cancelled': 'ملغي'
        }.get(lease.status, lease.status)
        
        # حساب الإيجار
        total_monthly_rent += lease.monthly_rent
        if lease.status == 'active':
            active_leases += 1
            style = 'success'
        elif lease.status == 'expiring_soon':
            style = 'warning'
        else:
            style = 'normal'
        
        exporter.add_row([
            idx,
            lease.contract_number,
            lease.tenant.name,
            f"{lease.unit.building.name} - {lease.unit.unit_number}",
            lease.monthly_rent,
            lease.start_date.strftime('%Y-%m-%d'),
            lease.end_date.strftime('%Y-%m-%d'),
            status_display
        ], style=style, number_formats=[None, None, None, None, 'currency', None, None, None])
    
    # الإحصائيات
    exporter.add_empty_row()
    exporter.add_total_row("إجمالي العقود", total_leases, col_span=len(headers), value_type='number')
    exporter.add_total_row("العقود النشطة", active_leases, col_span=len(headers), value_type='number')
    exporter.add_total_row("إجمالي الإيجار الشهري", total_monthly_rent, col_span=len(headers), value_type='currency')
    
    # النسب المئوية
    if total_leases > 0:
        active_percentage = round((active_leases / total_leases) * 100, 2)
        exporter.add_percentage_row("نسبة العقود النشطة", active_percentage, col_span=len(headers))
    
    # عرض الأعمدة
    exporter.set_column_widths([8, 15, 30.8, 12, 18, 15, 15, 18])
    
    return exporter.get_response("قائمة_العقود.xlsx")


@login_required
@user_passes_test(staff_required)
def export_payments_excel(request):
    """تصدير قائمة المدفوعات إلى Excel"""
    exporter = ExcelExporter("قائمة المدفوعات")
    
    # العناوين
    headers = ["#", "رقم العقد", "المستأجر", "المبلغ", "تاريخ الدفع", "الشهر", "طريقة الدفع", "حالة الشيك"]
    
    # العنوان
    exporter.add_title("قائمة المدفوعات", num_columns=len(headers))
    exporter.add_empty_row()
    
    exporter.create_header(headers)
    
    # البيانات
    payments = Payment.objects.all().select_related('lease', 'lease__tenant').order_by('-payment_date')
    total_payments = payments.count()
    total_amount = Decimal('0')
    cash_amount = Decimal('0')
    check_amount = Decimal('0')
    
    for idx, payment in enumerate(payments, 1):
        payment_method_display = {
            'cash': 'نقدي',
            'check': 'شيك',
            'bank_transfer': 'تحويل بنكي'
        }.get(payment.payment_method, payment.payment_method)
        
        check_status_display = "-"
        if payment.payment_method == 'check':
            check_status_display = {
                'pending': 'معلق',
                'cashed': 'تم الصرف',
                'returned': 'مرتجع'
            }.get(payment.check_status, payment.check_status or '-')
        
        total_amount += payment.amount
        if payment.payment_method == 'cash':
            cash_amount += payment.amount
        elif payment.payment_method == 'check':
            check_amount += payment.amount
        
        exporter.add_row([
            idx,
            payment.lease.contract_number,
            payment.lease.tenant.name,
            payment.amount,
            payment.payment_date.strftime('%Y-%m-%d'),
            f"{payment.payment_for_month}/{payment.payment_for_year}",
            payment_method_display,
            check_status_display
        ], number_formats=[None, None, None, 'currency', None, None, None, None])
    
    # الإحصائيات
    exporter.add_empty_row()
    exporter.add_total_row("إجمالي المدفوعات", total_payments, col_span=len(headers), value_type='number')
    exporter.add_total_row("إجمالي المبالغ", total_amount, col_span=len(headers), value_type='currency')
    exporter.add_total_row("المدفوعات النقدية", cash_amount, col_span=len(headers), value_type='currency')
    exporter.add_total_row("مدفوعات الشيكات", check_amount, col_span=len(headers), value_type='currency')
    
    # النسب المئوية
    if total_amount > 0:
        cash_percentage = round((cash_amount / total_amount) * 100, 2)
        check_percentage = round((check_amount / total_amount) * 100, 2)
        exporter.add_percentage_row("نسبة المدفوعات النقدية", cash_percentage, col_span=len(headers))
        exporter.add_percentage_row("نسبة مدفوعات الشيكات", check_percentage, col_span=len(headers))
    
    # عرض الأعمدة
    exporter.set_column_widths([8, 15, 25, 15, 15, 12, 18, 18])
    
    return exporter.get_response("قائمة_المدفوعات.xlsx")


@login_required
@user_passes_test(staff_required)
def export_expenses_excel(request):
    """تصدير قائمة المصروفات إلى Excel"""
    exporter = ExcelExporter("قائمة المصروفات")
    
    # العناوين
    headers = ["#", "المبنى", "الفئة", "الوصف", "المبلغ", "تاريخ المصروف"]
    
    # العنوان
    exporter.add_title("قائمة المصروفات", num_columns=len(headers))
    exporter.add_empty_row()
    
    exporter.create_header(headers)
    
    # البيانات
    expenses = Expense.objects.all().select_related('building').order_by('-expense_date')
    total_expenses = expenses.count()
    total_amount = Decimal('0')
    category_totals = {}
    
    for idx, expense in enumerate(expenses, 1):
        category_display = {
            'maintenance': 'صيانة',
            'utilities': 'مرافق',
            'insurance': 'تأمين',
            'taxes': 'ضرائب',
            'other': 'أخرى'
        }.get(expense.category, expense.category)
        
        total_amount += expense.amount
        
        # حساب مجموع كل فئة
        if category_display not in category_totals:
            category_totals[category_display] = Decimal('0')
        category_totals[category_display] += expense.amount
        
        exporter.add_row([
            idx,
            expense.building.name if expense.building else "-",
            category_display,
            expense.description,
            expense.amount,
            expense.expense_date.strftime('%Y-%m-%d')
        ], number_formats=[None, None, None, None, 'currency', None])
    
    # الإحصائيات
    exporter.add_empty_row()
    exporter.add_total_row("إجمالي المصروفات", total_expenses, col_span=len(headers), value_type='number')
    exporter.add_total_row("إجمالي المبالغ", total_amount, col_span=len(headers), value_type='currency')
    
    # مجموع كل فئة
    for category, amount in category_totals.items():
        exporter.add_total_row(f"مجموع {category}", amount, col_span=len(headers), value_type='currency')
    
    # النسب المئوية
    if total_amount > 0:
        exporter.add_empty_row()
        for category, amount in category_totals.items():
            percentage = round((amount / total_amount) * 100, 2)
            exporter.add_percentage_row(f"نسبة {category}", percentage, col_span=len(headers))
    
    # عرض الأعمدة
    exporter.set_column_widths([8, 25, 18, 40, 15, 15])
    
    return exporter.get_response("قائمة_المصروفات.xlsx")


@login_required
@user_passes_test(staff_required)
def export_buildings_excel(request):
    """تصدير قائمة المباني إلى Excel"""
    exporter = ExcelExporter("قائمة المباني")
    
    # العناوين
    headers = ["#", "اسم المبنى", "العنوان", "عدد الوحدات", "الوحدات المشغولة", "الوحدات المتاحة", "نسبة الإشغال"]
    
    # العنوان
    exporter.add_title("قائمة المباني والوحدات", num_columns=len(headers))
    exporter.add_empty_row()
    
    exporter.create_header(headers)
    
    # البيانات
    buildings = Building.objects.all().order_by('name')
    total_buildings = buildings.count()
    total_units = 0
    total_occupied = 0
    total_available = 0
    
    for idx, building in enumerate(buildings, 1):
        units = Unit.objects.filter(building=building)
        units_count = units.count()
        occupied = units.filter(is_available=False).count()
        available = units.filter(is_available=True).count()
        occupancy_rate = round((occupied / units_count * 100), 2) if units_count > 0 else 0
        
        total_units += units_count
        total_occupied += occupied
        total_available += available
        
        # تحديد النمط حسب نسبة الإشغال
        if occupancy_rate >= 80:
            style = 'success'
        elif occupancy_rate >= 50:
            style = 'normal'
        else:
            style = 'warning'
        
        exporter.add_row([
            idx,
            building.name,
            building.address,
            units_count,
            occupied,
            available,
            occupancy_rate
        ], style=style, number_formats=[None, None, None, None, None, None, 'percentage'])
    
    # الإحصائيات
    exporter.add_empty_row()
    exporter.add_total_row("إجمالي المباني", total_buildings, col_span=len(headers))
    exporter.add_total_row("إجمالي الوحدات", total_units, col_span=len(headers))
    exporter.add_total_row("الوحدات المشغولة", total_occupied, col_span=len(headers))
    exporter.add_total_row("الوحدات المتاحة", total_available, col_span=len(headers))
    
    # النسب المئوية
    if total_units > 0:
        overall_occupancy = round((total_occupied / total_units) * 100, 2)
        exporter.add_percentage_row("نسبة الإشغال الإجمالية", overall_occupancy, col_span=len(headers))
    
    # عرض الأعمدة
    exporter.set_column_widths([8, 25, 40, 18, 18, 18, 18])
    
    return exporter.get_response("قائمة_المباني.xlsx")


@login_required
@user_passes_test(staff_required)
def export_units_excel(request):
    """تصدير قائمة الوحدات إلى Excel"""
    exporter = ExcelExporter("قائمة الوحدات")
    
    # العناوين
    headers = ["#", "المبنى", "رقم الوحدة", "النوع", "الطابق", "الحالة", "المستأجر الحالي", "الإيجار الشهري"]
    
    # العنوان
    exporter.add_title("قائمة الوحدات", num_columns=len(headers))
    exporter.add_empty_row()
    
    exporter.create_header(headers)
    
    # البيانات
    units = Unit.objects.all().select_related('building').order_by('building', 'unit_number')
    total_units = units.count()
    available_units = 0
    occupied_units = 0
    total_rent = Decimal('0')
    
    for idx, unit in enumerate(units, 1):
        unit_type_display = {
            'office': 'مكتب',
            'apartment': 'شقة',
            'shop': 'محل'
        }.get(unit.unit_type, unit.unit_type)
        
        status_display = "متاحة" if unit.is_available else "مشغولة"
        
        # البحث عن المستأجر الحالي
        current_lease = Lease.objects.filter(
            unit=unit, 
            status__in=['active', 'expiring_soon']
        ).first()
        
        tenant_name = "-"
        monthly_rent = None
        
        if current_lease:
            tenant_name = current_lease.tenant.name
            monthly_rent = current_lease.monthly_rent
            total_rent += current_lease.monthly_rent
            occupied_units += 1
            style = 'success'
        else:
            available_units += 1
            style = 'normal'
        
        exporter.add_row([
            idx,
            unit.building.name,
            unit.unit_number,
            unit_type_display,
            unit.floor,
            status_display,
            tenant_name,
            monthly_rent if monthly_rent else "-"
        ], style=style, number_formats=[None, None, None, None, None, None, None, 'currency'])
    
    # الإحصائيات
    exporter.add_empty_row()
    exporter.add_total_row("إجمالي الوحدات", total_units, col_span=len(headers), value_type='number')
    exporter.add_total_row("الوحدات المشغولة", occupied_units, col_span=len(headers), value_type='number')
    exporter.add_total_row("الوحدات المتاحة", available_units, col_span=len(headers), value_type='number')
    exporter.add_total_row("إجمالي الإيجار الشهري", total_rent, col_span=len(headers), value_type='currency')
    
    # النسب المئوية
    if total_units > 0:
        occupancy_percentage = round((occupied_units / total_units) * 100, 2)
        exporter.add_percentage_row("نسبة الإشغال", occupancy_percentage, col_span=len(headers))
    
    # عرض الأعمدة
    exporter.set_column_widths([8, 25, 15, 15, 10, 15, 25, 18])
    
    return exporter.get_response("قائمة_الوحدات.xlsx")


@login_required
@user_passes_test(staff_required)
def export_maintenance_excel(request):
    """تصدير قائمة طلبات الصيانة إلى Excel"""
    exporter = ExcelExporter("طلبات الصيانة")
    
    # العناوين
    headers = ["#", "العنوان", "المستأجر", "الوحدة", "الأولوية", "الحالة", "تاريخ الإبلاغ"]
    
    # العنوان
    exporter.add_title("قائمة طلبات الصيانة", num_columns=len(headers))
    exporter.add_empty_row()
    
    exporter.create_header(headers)
    
    # البيانات
    requests = MaintenanceRequest.objects.all().select_related('lease', 'lease__tenant', 'lease__unit').order_by('-reported_date')
    total_requests = requests.count()
    pending_count = 0
    in_progress_count = 0
    completed_count = 0
    
    for idx, req in enumerate(requests, 1):
        priority_display = {
            'low': 'منخفضة',
            'medium': 'متوسطة',
            'high': 'عالية'
        }.get(req.priority, req.priority)
        
        status_display = {
            'pending': 'معلق',
            'in_progress': 'قيد التنفيذ',
            'completed': 'مكتمل'
        }.get(req.status, req.status)
        
        # حساب الإحصائيات
        if req.status == 'pending':
            pending_count += 1
            style = 'warning'
        elif req.status == 'in_progress':
            in_progress_count += 1
            style = 'normal'
        else:
            completed_count += 1
            style = 'success'
        
        exporter.add_row([
            idx,
            req.title,
            req.lease.tenant.name,
            f"{req.lease.unit.building.name} - {req.lease.unit.unit_number}",
            priority_display,
            status_display,
            req.reported_date.strftime('%Y-%m-%d')
        ], style=style)
    
    # الإحصائيات
    exporter.add_empty_row()
    exporter.add_total_row("إجمالي الطلبات", total_requests, col_span=len(headers))
    exporter.add_total_row("طلبات معلقة", pending_count, col_span=len(headers))
    exporter.add_total_row("طلبات قيد التنفيذ", in_progress_count, col_span=len(headers))
    exporter.add_total_row("طلبات مكتملة", completed_count, col_span=len(headers))
    
    # النسب المئوية
    if total_requests > 0:
        completion_rate = round((completed_count / total_requests) * 100, 2)
        exporter.add_percentage_row("نسبة الإنجاز", completion_rate, col_span=len(headers))
    
    # عرض الأعمدة
    exporter.set_column_widths([8, 30, 25, 30, 15, 18, 18])
    
    return exporter.get_response("طلبات_الصيانة.xlsx")

@login_required
@user_passes_test(staff_required)
def export_comprehensive_report(request):
    """تصدير تقرير شامل يحتوي على جميع التقارير في ملف واحد
    Comprehensive Report - All Reports in One File"""
    
    wb = Workbook()
    wb.remove(wb.active)
    
    # الترجمات
    translations = {
        'tenants': {'ar': 'المستأجرين', 'en': 'Tenants'},
        'leases': {'ar': 'العقود', 'en': 'Leases'},
        'payments': {'ar': 'المدفوعات', 'en': 'Payments'},
        'expenses': {'ar': 'المصروفات', 'en': 'Expenses'},
        'buildings': {'ar': 'المباني', 'en': 'Buildings'},
        'units': {'ar': 'الوحدات', 'en': 'Units'},
        'maintenance': {'ar': 'الصيانة', 'en': 'Maintenance'},
    }
    
    # 1. ورقة المستأجرين (Tenants)
    ws_tenants = wb.create_sheet(f"{translations['tenants']['ar']} | {translations['tenants']['en']}")
    _create_tenants_sheet(ws_tenants)
    
    # 2. ورقة العقود (Leases)
    ws_leases = wb.create_sheet(f"{translations['leases']['ar']} | {translations['leases']['en']}")
    _create_leases_sheet(ws_leases)
    
    # 3. ورقة المدفوعات (Payments)
    ws_payments = wb.create_sheet(f"{translations['payments']['ar']} | {translations['payments']['en']}")
    _create_payments_sheet(ws_payments)
    
    # 4. ورقة المصروفات (Expenses)
    ws_expenses = wb.create_sheet(f"{translations['expenses']['ar']} | {translations['expenses']['en']}")
    _create_expenses_sheet(ws_expenses)
    
    # 5. ورقة المباني (Buildings)
    ws_buildings = wb.create_sheet(f"{translations['buildings']['ar']} | {translations['buildings']['en']}")
    _create_buildings_sheet(ws_buildings)
    
    # 6. ورقة الوحدات (Units)
    ws_units = wb.create_sheet(f"{translations['units']['ar']} | {translations['units']['en']}")
    _create_units_sheet(ws_units)
    
    # 7. ورقة طلبات الصيانة (Maintenance)
    ws_maintenance = wb.create_sheet(f"{translations['maintenance']['ar']} | {translations['maintenance']['en']}")
    _create_maintenance_sheet(ws_maintenance)
    
    # حفظ الملف
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"تقرير_شامل_Comprehensive_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    
    return response


def _create_tenants_sheet(ws):
    """إنشاء ورقة المستأجرين"""
    exporter = ExcelExporter("قائمة المستأجرين | Tenants List")
    exporter.ws = ws
    
    headers = ["# | No.", "الاسم | Name", "النوع | Type", "الهاتف | Phone", 
               "البريد | Email", "المفوض | Authorized", "التقييم | Rating"]
    
    exporter.add_title("قائمة المستأجرين", subtitle="Tenants List", num_columns=len(headers), include_logo=False)
    exporter.add_empty_row()
    exporter.create_header(headers)
    
    tenants = Tenant.objects.all().order_by('name')
    for idx, tenant in enumerate(tenants, 1):
        tenant_type = "فرد | Individual" if tenant.tenant_type == 'individual' else "شركة | Company"
        exporter.add_row([
            idx,
            tenant.name,
            tenant_type,
            tenant.phone,
            tenant.email or "-",
            tenant.authorized_signatory or "-",
            f"{'⭐' * tenant.rating} ({tenant.rating}/5)"
        ])
    
    exporter.add_empty_row()
    exporter.add_total_row("إجمالي | Total", tenants.count(), col_span=len(headers))
    exporter.set_column_widths([8, 25, 20, 18, 30, 25, 18])


def _create_leases_sheet(ws):
    """إنشاء ورقة العقود"""
    exporter = ExcelExporter("قائمة العقود | Leases List")
    exporter.ws = ws
    
    headers = ["# | No.", "رقم العقد | Contract No.", "المستأجر | Tenant", "الوحدة | Unit", 
               "الإيجار | Rent", "البدء | Start", "الانتهاء | End", "الحالة | Status"]
    
    exporter.add_title("قائمة العقود", subtitle="Leases List", num_columns=len(headers), include_logo=False)
    exporter.add_empty_row()
    exporter.create_header(headers)
    
    leases = Lease.objects.all().select_related('tenant', 'unit', 'unit__building').order_by('-start_date')
    total_rent = Decimal('0')
    active_count = 0
    
    for idx, lease in enumerate(leases, 1):
        status_map = {
            'active': 'نشط | Active',
            'expiring_soon': 'ينتهي قريباً | Expiring',
            'expired': 'منتهي | Expired',
            'cancelled': 'ملغي | Cancelled'
        }
        status = status_map.get(lease.status, lease.status)
        
        total_rent += lease.monthly_rent
        if lease.status == 'active':
            active_count += 1
            style = 'success'
        elif lease.status == 'expiring_soon':
            style = 'warning'
        else:
            style = 'normal'
        
        exporter.add_row([
            idx,
            lease.contract_number,
            lease.tenant.name,
            f"{lease.unit.building.name} - {lease.unit.unit_number}",
            lease.monthly_rent,
            lease.start_date.strftime('%Y-%m-%d'),
            lease.end_date.strftime('%Y-%m-%d'),
            status
        ], style=style, number_formats=[None, None, None, None, 'currency', None, None, None])
    
    exporter.add_empty_row()
    exporter.add_total_row("إجمالي العقود | Total Leases", leases.count(), col_span=len(headers))
    exporter.add_total_row("العقود النشطة | Active Leases", active_count, col_span=len(headers))
    exporter.add_total_row("إجمالي الإيجار | Total Rent", total_rent, col_span=len(headers), value_type='currency')
    
    if leases.count() > 0:
        active_percentage = round((active_count / leases.count()) * 100, 2)
        exporter.add_percentage_row("نسبة العقود النشطة | Active Rate", active_percentage, col_span=len(headers))
    
    exporter.set_column_widths([8, 18, 25, 30, 18, 15, 15, 20])


def _create_payments_sheet(ws):
    """إنشاء ورقة المدفوعات"""
    exporter = ExcelExporter("قائمة المدفوعات | Payments List")
    exporter.ws = ws
    
    headers = ["# | No.", "رقم العقد | Contract", "المستأجر | Tenant", "المبلغ | Amount", 
               "التاريخ | Date", "الشهر | Month", "الطريقة | Method", "حالة الشيك | Check Status"]
    
    exporter.add_title("قائمة المدفوعات", subtitle="Payments List", num_columns=len(headers), include_logo=False)
    exporter.add_empty_row()
    exporter.create_header(headers)
    
    payments = Payment.objects.all().select_related('lease', 'lease__tenant').order_by('-payment_date')
    total_amount = Decimal('0')
    
    for idx, payment in enumerate(payments, 1):
        method_map = {
            'cash': 'نقدي | Cash',
            'check': 'شيك | Check',
            'bank_transfer': 'تحويل | Transfer'
        }
        method = method_map.get(payment.payment_method, payment.payment_method)
        
        check_status = "-"
        if payment.payment_method == 'check':
            status_map = {
                'pending': 'معلق | Pending',
                'cashed': 'صرف | Cashed',
                'returned': 'مرتجع | Returned'
            }
            check_status = status_map.get(payment.check_status, payment.check_status or '-')
        
        total_amount += payment.amount
        
        exporter.add_row([
            idx,
            payment.lease.contract_number,
            payment.lease.tenant.name,
            payment.amount,
            payment.payment_date.strftime('%Y-%m-%d'),
            f"{payment.payment_for_month}/{payment.payment_for_year}",
            method,
            check_status
        ], number_formats=[None, None, None, 'currency', None, None, None, None])
    
    exporter.add_empty_row()
    exporter.add_total_row("إجمالي المدفوعات | Total Payments", payments.count(), col_span=len(headers))
    exporter.add_total_row("إجمالي المبلغ | Total Amount", total_amount, col_span=len(headers), value_type='currency')
    
    exporter.set_column_widths([8, 18, 25, 18, 15, 15, 20, 20])


def _create_expenses_sheet(ws):
    """إنشاء ورقة المصروفات"""
    exporter = ExcelExporter("قائمة المصروفات | Expenses List")
    exporter.ws = ws
    
    headers = ["# | No.", "المبنى | Building", "الفئة | Category", 
               "الوصف | Description", "المبلغ | Amount", "التاريخ | Date"]
    
    exporter.add_title("قائمة المصروفات", subtitle="Expenses List", num_columns=len(headers), include_logo=False)
    exporter.add_empty_row()
    exporter.create_header(headers)
    
    expenses = Expense.objects.all().select_related('building').order_by('-expense_date')
    total_amount = Decimal('0')
    
    for idx, expense in enumerate(expenses, 1):
        category_map = {
            'maintenance': 'صيانة | Maintenance',
            'utilities': 'مرافق | Utilities',
            'insurance': 'تأمين | Insurance',
            'taxes': 'ضرائب | Taxes',
            'other': 'أخرى | Other'
        }
        category = category_map.get(expense.category, expense.category)
        
        total_amount += expense.amount
        
        exporter.add_row([
            idx,
            expense.building.name if expense.building else "-",
            category,
            expense.description,
            expense.amount,
            expense.expense_date.strftime('%Y-%m-%d')
        ], number_formats=[None, None, None, None, 'currency', None])
    
    exporter.add_empty_row()
    exporter.add_total_row("إجمالي المصروفات | Total Expenses", expenses.count(), col_span=len(headers))
    exporter.add_total_row("إجمالي المبلغ | Total Amount", total_amount, col_span=len(headers), value_type='currency')
    
    exporter.set_column_widths([8, 25, 20, 40, 18, 15])


def _create_buildings_sheet(ws):
    """إنشاء ورقة المباني"""
    exporter = ExcelExporter("قائمة المباني | Buildings List")
    exporter.ws = ws
    
    headers = ["# | No.", "المبنى | Building", "العنوان | Address", "الوحدات | Units", 
               "مشغول | Occupied", "متاح | Available", "نسبة الإشغال | Occupancy %"]
    
    exporter.add_title("قائمة المباني", subtitle="Buildings List", num_columns=len(headers), include_logo=False)
    exporter.add_empty_row()
    exporter.create_header(headers)
    
    buildings = Building.objects.all().order_by('name')
    total_units = 0
    total_occupied = 0
    
    for idx, building in enumerate(buildings, 1):
        units = Unit.objects.filter(building=building)
        units_count = units.count()
        occupied = units.filter(is_available=False).count()
        available = units.filter(is_available=True).count()
        occupancy_rate = round((occupied / units_count * 100), 2) if units_count > 0 else 0
        
        total_units += units_count
        total_occupied += occupied
        
        style = 'success' if occupancy_rate >= 80 else ('normal' if occupancy_rate >= 50 else 'warning')
        
        exporter.add_row([
            idx,
            building.name,
            building.address,
            units_count,
            occupied,
            available,
            occupancy_rate
        ], style=style, number_formats=[None, None, None, None, None, None, 'percentage'])
    
    exporter.add_empty_row()
    exporter.add_total_row("إجمالي المباني | Total Buildings", buildings.count(), col_span=len(headers))
    exporter.add_total_row("إجمالي الوحدات | Total Units", total_units, col_span=len(headers))
    
    if total_units > 0:
        overall_occupancy = round((total_occupied / total_units) * 100, 2)
        exporter.add_percentage_row("نسبة الإشغال الكلية | Overall Occupancy", overall_occupancy, col_span=len(headers))
    
    exporter.set_column_widths([8, 25, 40, 15, 15, 15, 20])


def _create_units_sheet(ws):
    """إنشاء ورقة الوحدات"""
    exporter = ExcelExporter("قائمة الوحدات | Units List")
    exporter.ws = ws
    
    headers = ["# | No.", "المبنى | Building", "رقم | Number", "النوع | Type", 
               "الطابق | Floor", "الحالة | Status", "المستأجر | Tenant", "الإيجار | Rent"]
    
    exporter.add_title("قائمة الوحدات", subtitle="Units List", num_columns=len(headers), include_logo=False)
    exporter.add_empty_row()
    exporter.create_header(headers)
    
    units = Unit.objects.all().select_related('building').order_by('building', 'unit_number')
    total_rent = Decimal('0')
    occupied_count = 0
    
    for idx, unit in enumerate(units, 1):
        type_map = {
            'office': 'مكتب | Office',
            'apartment': 'شقة | Apartment',
            'shop': 'محل | Shop'
        }
        unit_type = type_map.get(unit.unit_type, unit.unit_type)
        
        status = "متاحة | Available" if unit.is_available else "مشغولة | Occupied"
        
        current_lease = Lease.objects.filter(
            unit=unit, 
            status__in=['active', 'expiring_soon']
        ).first()
        
        tenant_name = "-"
        monthly_rent = None
        style = 'normal'
        
        if current_lease:
            tenant_name = current_lease.tenant.name
            monthly_rent = current_lease.monthly_rent
            total_rent += current_lease.monthly_rent
            occupied_count += 1
            style = 'success'
        
        exporter.add_row([
            idx,
            unit.building.name,
            unit.unit_number,
            unit_type,
            unit.floor,
            status,
            tenant_name,
            monthly_rent if monthly_rent else "-"
        ], style=style, number_formats=[None, None, None, None, None, None, None, 'currency'])
    
    exporter.add_empty_row()
    exporter.add_total_row("إجمالي الوحدات | Total Units", units.count(), col_span=len(headers))
    exporter.add_total_row("الوحدات المشغولة | Occupied Units", occupied_count, col_span=len(headers))
    exporter.add_total_row("إجمالي الإيجار | Total Rent", total_rent, col_span=len(headers), value_type='currency')
    
    if units.count() > 0:
        occupancy = round((occupied_count / units.count()) * 100, 2)
        exporter.add_percentage_row("نسبة الإشغال | Occupancy Rate", occupancy, col_span=len(headers))
    
    exporter.set_column_widths([8, 25, 15, 20, 12, 20, 25, 18])


def _create_maintenance_sheet(ws):
    """إنشاء ورقة طلبات الصيانة"""
    exporter = ExcelExporter("طلبات الصيانة | Maintenance Requests")
    exporter.ws = ws
    
    headers = ["# | No.", "العنوان | Title", "المستأجر | Tenant", "الوحدة | Unit", 
               "الأولوية | Priority", "الحالة | Status", "التاريخ | Date"]
    
    exporter.add_title("طلبات الصيانة", subtitle="Maintenance Requests", num_columns=len(headers), include_logo=False)
    exporter.add_empty_row()
    exporter.create_header(headers)
    
    requests = MaintenanceRequest.objects.all().select_related('lease', 'lease__tenant', 'lease__unit').order_by('-reported_date')
    pending_count = 0
    in_progress_count = 0
    completed_count = 0
    
    for idx, req in enumerate(requests, 1):
        priority_map = {
            'low': 'منخفضة | Low',
            'medium': 'متوسطة | Medium',
            'high': 'عالية | High'
        }
        priority = priority_map.get(req.priority, req.priority)
        
        status_map = {
            'pending': 'معلق | Pending',
            'in_progress': 'قيد التنفيذ | In Progress',
            'completed': 'مكتمل | Completed'
        }
        status = status_map.get(req.status, req.status)
        
        if req.status == 'pending':
            pending_count += 1
            style = 'warning'
        elif req.status == 'in_progress':
            in_progress_count += 1
            style = 'normal'
        else:
            completed_count += 1
            style = 'success'
        
        exporter.add_row([
            idx,
            req.title,
            req.lease.tenant.name,
            f"{req.lease.unit.building.name} - {req.lease.unit.unit_number}",
            priority,
            status,
            req.reported_date.strftime('%Y-%m-%d')
        ], style=style)
    
    exporter.add_empty_row()
    exporter.add_total_row("إجمالي الطلبات | Total Requests", requests.count(), col_span=len(headers))
    exporter.add_total_row("معلقة | Pending", pending_count, col_span=len(headers))
    exporter.add_total_row("قيد التنفيذ | In Progress", in_progress_count, col_span=len(headers))
    exporter.add_total_row("مكتملة | Completed", completed_count, col_span=len(headers))
    
    if requests.count() > 0:
        completion_rate = round((completed_count / requests.count()) * 100, 2)
        exporter.add_percentage_row("نسبة الإنجاز | Completion Rate", completion_rate, col_span=len(headers))
    
    exporter.set_column_widths([8, 30, 25, 30, 20, 20, 15])


@login_required
@user_passes_test(staff_required)
def export_comprehensive_pdf_report(request):
    """تصدير تقرير PDF شامل يحتوي على جميع التقارير
    Comprehensive PDF Report - All Reports in One File"""
    
    from .pdf_utils import PDFReportGenerator
    from .models import Company
    
    # إنشاء مولد التقرير
    pdf = PDFReportGenerator(
        title_ar="التقرير الشامل لإدارة الإيجارات",
        title_en="Comprehensive Rental Management Report",
        orientation='landscape'
    )
    
    # محاولة إضافة شعار الشركة
    logo_found = False
    try:
        # محاولة 1: من نموذج Company
        company = Company.objects.first()
        if company and company.logo:
            pdf.set_logo(company.logo.path)
            logo_found = True
    except:
        pass
    
    # محاولة 2: من مسارات افتراضية
    if not logo_found:
        possible_paths = [
            'static/images/logo.png',
            'static/images/company_logo.png',
            'media/company_logo.png',
            'static/logo.png',
        ]
        import os
        from django.conf import settings
        
        for path in possible_paths:
            full_path = os.path.join(settings.BASE_DIR, path)
            if os.path.exists(full_path):
                pdf.set_logo(full_path)
                break
    
    # إضافة الترويسة
    pdf.add_header(include_logo=True)
    
    # 1. قسم المستأجرين
    pdf.add_section_title("قائمة المستأجرين", "Tenants List")
    tenants = Tenant.objects.all().order_by('name')
    tenants_data = []
    for idx, tenant in enumerate(tenants, 1):
        tenant_type = "فرد | Individual" if tenant.tenant_type == 'individual' else "شركة | Company"
        tenants_data.append([
            str(idx),
            tenant.name,
            tenant_type,
            tenant.phone,
            tenant.email or "-",
            f"{'⭐' * tenant.rating} ({tenant.rating}/5)"
        ])
    
    pdf.add_table(
        headers=["# | No.", "الاسم | Name", "النوع | Type", "الهاتف | Phone", "البريد | Email", "التقييم | Rating"],
        data=tenants_data,
        col_widths=[0.5*inch, 1.8*inch, 1.3*inch, 1.2*inch, 1.8*inch, 1.2*inch]
    )
    
    pdf.add_summary_table([
        ("إجمالي المستأجرين", "Total Tenants", tenants.count())
    ])
    
    # 2. قسم العقود
    pdf.add_page_break()
    pdf.add_section_title("قائمة العقود", "Leases List")
    leases = Lease.objects.all().select_related('tenant', 'unit', 'unit__building').order_by('-start_date')[:50]
    
    leases_data = []
    total_rent = Decimal('0')
    active_count = 0
    
    for idx, lease in enumerate(leases, 1):
        status_map = {
            'active': 'نشط | Active',
            'expiring_soon': 'ينتهي | Expiring',
            'expired': 'منتهي | Expired',
            'cancelled': 'ملغي | Cancelled'
        }
        status = status_map.get(lease.status, lease.status)
        
        total_rent += lease.monthly_rent
        if lease.status == 'active':
            active_count += 1
        
        leases_data.append([
            str(idx),
            lease.contract_number,
            lease.tenant.name,
            f"{lease.unit.building.name} - {lease.unit.unit_number}",
            pdf.format_currency(lease.monthly_rent),
            lease.start_date.strftime('%Y-%m-%d'),
            status
        ])
    
    pdf.add_table(
        headers=["#", "رقم العقد | Contract", "المستأجر | Tenant", "الوحدة | Unit", 
                "الإيجار | Rent", "البدء | Start", "الحالة | Status"],
        data=leases_data,
        col_widths=[0.4*inch, 1*inch, 1.5*inch, 1.8*inch, 1.2*inch, 1*inch, 1.3*inch]
    )
    
    pdf.add_summary_table([
        ("إجمالي العقود", "Total Leases", Lease.objects.count()),
        ("العقود النشطة", "Active Leases", active_count),
        ("إجمالي الإيجار الشهري", "Total Monthly Rent", pdf.format_currency(total_rent))
    ])
    
    # 3. قسم المدفوعات
    pdf.add_page_break()
    pdf.add_section_title("قائمة المدفوعات", "Payments List")
    payments = Payment.objects.all().select_related('lease', 'lease__tenant').order_by('-payment_date')[:50]
    
    payments_data = []
    total_amount = Decimal('0')
    
    for idx, payment in enumerate(payments, 1):
        method_map = {
            'cash': 'نقدي | Cash',
            'check': 'شيك | Check',
            'bank_transfer': 'تحويل | Transfer'
        }
        method = method_map.get(payment.payment_method, payment.payment_method)
        
        total_amount += payment.amount
        
        payments_data.append([
            str(idx),
            payment.lease.contract_number,
            payment.lease.tenant.name,
            pdf.format_currency(payment.amount),
            payment.payment_date.strftime('%Y-%m-%d'),
            f"{payment.payment_for_month}/{payment.payment_for_year}",
            method
        ])
    
    pdf.add_table(
        headers=["#", "رقم العقد | Contract", "المستأجر | Tenant", "المبلغ | Amount", 
                "التاريخ | Date", "الشهر | Month", "الطريقة | Method"],
        data=payments_data,
        col_widths=[0.4*inch, 1*inch, 1.5*inch, 1.2*inch, 1*inch, 0.9*inch, 1.3*inch]
    )
    
    pdf.add_summary_table([
        ("إجمالي المدفوعات", "Total Payments", Payment.objects.count()),
        ("إجمالي المبلغ", "Total Amount", pdf.format_currency(total_amount))
    ])
    
    # 4. قسم المصروفات
    pdf.add_page_break()
    pdf.add_section_title("قائمة المصروفات", "Expenses List")
    expenses = Expense.objects.all().select_related('building').order_by('-expense_date')[:50]
    
    expenses_data = []
    total_expense = Decimal('0')
    
    for idx, expense in enumerate(expenses, 1):
        category_map = {
            'maintenance': 'صيانة | Maintenance',
            'utilities': 'مرافق | Utilities',
            'insurance': 'تأمين | Insurance',
            'taxes': 'ضرائب | Taxes',
            'other': 'أخرى | Other'
        }
        category = category_map.get(expense.category, expense.category)
        
        total_expense += expense.amount
        
        expenses_data.append([
            str(idx),
            expense.building.name if expense.building else "-",
            category,
            expense.description[:40] + "..." if len(expense.description) > 40 else expense.description,
            pdf.format_currency(expense.amount),
            expense.expense_date.strftime('%Y-%m-%d')
        ])
    
    pdf.add_table(
        headers=["#", "المبنى | Building", "الفئة | Category", "الوصف | Description", 
                "المبلغ | Amount", "التاريخ | Date"],
        data=expenses_data,
        col_widths=[0.4*inch, 1.3*inch, 1.3*inch, 2.2*inch, 1.2*inch, 1*inch]
    )
    
    pdf.add_summary_table([
        ("إجمالي المصروفات", "Total Expenses", Expense.objects.count()),
        ("إجمالي المبلغ", "Total Amount", pdf.format_currency(total_expense))
    ])
    
    # 5. قسم المباني
    pdf.add_page_break()
    pdf.add_section_title("قائمة المباني", "Buildings List")
    buildings = Building.objects.all().order_by('name')
    
    buildings_data = []
    total_units = 0
    total_occupied = 0
    
    for idx, building in enumerate(buildings, 1):
        units = Unit.objects.filter(building=building)
        units_count = units.count()
        occupied = units.filter(is_available=False).count()
        available = units.filter(is_available=True).count()
        occupancy_rate = round((occupied / units_count * 100), 1) if units_count > 0 else 0
        
        total_units += units_count
        total_occupied += occupied
        
        buildings_data.append([
            str(idx),
            building.name,
            building.address[:30] + "..." if len(building.address) > 30 else building.address,
            str(units_count),
            str(occupied),
            str(available),
            f"{occupancy_rate}%"
        ])
    
    pdf.add_table(
        headers=["#", "المبنى | Building", "العنوان | Address", "الوحدات | Units", 
                "مشغول | Occupied", "متاح | Available", "نسبة الإشغال | Occupancy"],
        data=buildings_data,
        col_widths=[0.4*inch, 1.5*inch, 2*inch, 0.9*inch, 0.9*inch, 0.9*inch, 1.2*inch]
    )
    
    overall_occupancy = round((total_occupied / total_units * 100), 1) if total_units > 0 else 0
    pdf.add_summary_table([
        ("إجمالي المباني", "Total Buildings", buildings.count()),
        ("إجمالي الوحدات", "Total Units", total_units),
        ("نسبة الإشغال الكلية", "Overall Occupancy", f"{overall_occupancy}%")
    ])
    
    # 6. قسم طلبات الصيانة
    pdf.add_page_break()
    pdf.add_section_title("طلبات الصيانة", "Maintenance Requests")
    maintenance_requests = MaintenanceRequest.objects.all().select_related(
        'lease', 'lease__tenant', 'lease__unit'
    ).order_by('-reported_date')[:50]
    
    maintenance_data = []
    pending_count = 0
    in_progress_count = 0
    completed_count = 0
    
    for idx, req in enumerate(maintenance_requests, 1):
        priority_map = {
            'low': 'منخفضة | Low',
            'medium': 'متوسطة | Medium',
            'high': 'عالية | High'
        }
        priority = priority_map.get(req.priority, req.priority)
        
        status_map = {
            'pending': 'معلق | Pending',
            'in_progress': 'قيد التنفيذ | In Progress',
            'completed': 'مكتمل | Completed'
        }
        status = status_map.get(req.status, req.status)
        
        if req.status == 'pending':
            pending_count += 1
        elif req.status == 'in_progress':
            in_progress_count += 1
        else:
            completed_count += 1
        
        maintenance_data.append([
            str(idx),
            req.title[:30] + "..." if len(req.title) > 30 else req.title,
            req.lease.tenant.name,
            f"{req.lease.unit.building.name} - {req.lease.unit.unit_number}",
            priority,
            status,
            req.reported_date.strftime('%Y-%m-%d')
        ])
    
    pdf.add_table(
        headers=["#", "العنوان | Title", "المستأجر | Tenant", "الوحدة | Unit", 
                "الأولوية | Priority", "الحالة | Status", "التاريخ | Date"],
        data=maintenance_data,
        col_widths=[0.4*inch, 1.8*inch, 1.3*inch, 1.5*inch, 1.2*inch, 1.3*inch, 1*inch]
    )
    
    completion_rate = round((completed_count / MaintenanceRequest.objects.count() * 100), 1) if MaintenanceRequest.objects.count() > 0 else 0
    pdf.add_summary_table([
        ("إجمالي الطلبات", "Total Requests", MaintenanceRequest.objects.count()),
        ("معلقة", "Pending", pending_count),
        ("قيد التنفيذ", "In Progress", in_progress_count),
        ("مكتملة", "Completed", completed_count),
        ("نسبة الإنجاز", "Completion Rate", f"{completion_rate}%")
    ])
    
    # بناء وإرجاع PDF
    return pdf.build(f"تقرير_شامل_Comprehensive_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
