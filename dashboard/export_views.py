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
