from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal
import datetime
from django.db.models import Sum

def get_next_voucher_number(prefix):
    today = timezone.now().date()
    year = today.year
    last_voucher = None
    if prefix == 'RCPT':
        last_voucher = Invoice.objects.filter(voucher_number__startswith=f"RCPT-{year}").order_by('-voucher_number').last()
    elif prefix == 'PV':
        last_voucher = Expense.objects.filter(voucher_number__startswith=f"PV-{year}").order_by('-voucher_number').last()

    if not last_voucher:
        return f"{prefix}-{year}-0001"

    last_num = int(last_voucher.voucher_number.split('-')[-1])
    new_num = last_num + 1
    return f"{prefix}-{year}-{new_num:04d}"

class Company(models.Model):
    name = models.CharField(_("اسم الشركة"), max_length=150, default="شركة إدارة الإيجارات")
    logo = models.ImageField(_("الشعار"), upload_to='company_logos/', blank=True, null=True)
    primary_color = models.CharField(_("اللون الأساسي"), max_length=7, default="#993333", help_text=_("مثال:#993333 "))
    secondary_color = models.CharField(_("اللون الثانوي"), max_length=7, default="#D4Af37", help_text=_("مثال:#333399 "))

    class Meta:
        verbose_name = _("ملف الشركة")
        verbose_name_plural = _("ملفات الشركة")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.pk = 1
        super(Company, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

class Building(models.Model):
    name = models.CharField(_("اسم المبنى"), max_length=100)
    address = models.TextField(_("العنوان"))
    
    class Meta:
        verbose_name = _("مبنى")
        verbose_name_plural = _("المباني")
        permissions = [("can_view_buildings_reports", _("يمكنه عرض تقارير المباني"))]
        
    def __str__(self):
        return self.name

class Unit(models.Model):
    UNIT_TYPE_CHOICES = [('office', _('مكتب')), ('apartment', _('شقة')), ('shop', _('محل'))]
    building = models.ForeignKey(Building, on_delete=models.CASCADE, verbose_name=_("المبنى"))
    unit_number = models.CharField(_("رقم الوحدة"), max_length=20)
    unit_type = models.CharField(_("نوع الوحدة"), max_length=20, choices=UNIT_TYPE_CHOICES)
    floor = models.IntegerField(_("الطابق"))
    is_available = models.BooleanField(_("متاحة للإيجار"), default=True)
    vacant_since = models.DateField(_("شاغرة منذ تاريخ"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("وحدة")
        verbose_name_plural = _("الوحدات")
        
    def __str__(self):
        return f"{self.building.name} - {self.unit_number}"

class Tenant(models.Model):
    TENANT_TYPE_CHOICES = [('individual', _('فرد')), ('company', _('شركة'))]
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("حساب المستخدم"), help_text=_("اربط المستأجر بحساب مستخدم لتسجيل الدخول إلى البوابة."))
    name = models.CharField(_("اسم المستأجر"), max_length=150)
    tenant_type = models.CharField(_("نوع المستأجر"), max_length=20, choices=TENANT_TYPE_CHOICES)
    phone = models.CharField(_("رقم الهاتف"), max_length=15)
    email = models.EmailField(_("البريد الإلكتروني"), blank=True, null=True)
    authorized_signatory = models.CharField(_("المفوض بالتوقيع"), max_length=150, blank=True, null=True, help_text=_("يُملأ فقط في حال كان المستأجر شركة"))
    commercial_reg_no = models.CharField(_("رقم السجل التجاري"), max_length=50, blank=True, null=True)
    tax_card_no = models.CharField(_("رقم البطاقة الضريبية"), max_length=50, blank=True, null=True)
    rating = models.PositiveIntegerField(_("تقيم العميل"), choices=[(i, str(i)) for i in range(1, 6)], default=3, help_text=_("تقيم داخلي للعميل من 1 إلى 5 نجوم"))
    internal_notes = models.TextField(_("ملاحظات داخلية"), blank=True, null=True, help_text=_("ملاحظات داخلية للموظفين فقط"))
    
    class Meta:
        verbose_name = _("مستأجر")
        verbose_name_plural = _("المستأجرين")
        permissions = [("can_view_tenant_portal", _("يمكنه عرض بوابة المستأجرين"))]

    def get_absolute_url(self):
        return reverse('tenant_detail', kwargs={'pk': self.pk})
        
    def __str__(self):
        return self.name

class Lease(models.Model):
    STATUS_CHOICES = [('active', _('نشط')), ('expiring_soon', _('قريب الانتهاء')), ('expired', _('منتهي')), ('cancelled', _('ملغي'))]
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, verbose_name=_("الوحدة"))
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, verbose_name=_("المستأجر"))
    contract_number = models.CharField(_("رقم العقد"), max_length=50, unique=True)
    contract_form_number = models.CharField(_("رقم نموذج العقد"), max_length=50, blank=True, null=True)
    monthly_rent = models.DecimalField(_("مبلغ الإيجار الشهري"), max_digits=10, decimal_places=2)
    start_date = models.DateField(_("تاريخ بدء العقد"))
    end_date = models.DateField(_("تاريخ انتهاء العقد"))
    electricity_meter = models.CharField(_("رقم عداد الكهرباء"), max_length=50, blank=True, null=True)
    water_meter = models.CharField(_("رقم عداد المياه"), max_length=50, blank=True, null=True)
    status = models.CharField(_("حالة العقد"), max_length=20, choices=STATUS_CHOICES, default='active', editable=False)
    office_fee = models.DecimalField(_("رسوم المكتب"), max_digits=10, decimal_places=2, default=5.00)
    admin_fee = models.DecimalField(_("الرسوم الإدارية"), max_digits=10, decimal_places=2, default=1.00)
    registration_fee = models.DecimalField(_("رسوم تسجيل العقد (3%)"), max_digits=10, decimal_places=2, blank=True)
    template = models.ForeignKey('ContractTemplate', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("قالب العقد المستخدم"))
    auto_renew = models.BooleanField(_("تجديد تلقائي عند الانتهاء"), default=False)
    cancellation_date = models.DateField(_("تاريخ الإلغاء"), blank=True, null=True)
    cancellation_reason = models.TextField(_("سبب الإلغاء"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("عقد إيجار")
        verbose_name_plural = _("عقود الإيجار")
        permissions = [("can_view_financial_summary", _("يمكنه عرض ملخص مالي")), ("canc_cancel_lease", _("يمكنه إلغاء عقد"))]
        
    def save(self, *args, **kwargs):
        self.registration_fee = (self.monthly_rent * 12) * Decimal('0.03')
        is_new = self._state.addin
        old_status = None
        if not is_new:
            old_lease = Lease.objects.get(pk=self.pk)
            old_status = old_lease.status
        self.update_status()
        super().save(*args, **kwargs)
        if is_new and self.status in ['active', 'expiring_soon']:
            self.unit.is_available = False
            self.unit.vacant_since = None
            self.unit.save()
        elif not is_new and old_status != self.status:
            is_active = self.status in ['active', 'expiring_soon']
            was_active_before = old_status in ['active', 'expiring_soon']
            if is_active and not was_active_before:
                self.unit.is_available = False
                self.unit.vacant_since = timezone.now().date()
        if self.pk:
            old_lease = Lease.objects.get(pk=self.pk)
            if old_lease.unit != self.unit:
                old_lease.unit.is_available = True
                old_lease.unit.save()
            if self.status in ['active', 'expiring_soon']:
                self.unit.is_available = False
            else:
                self.unit.is_available = True
            self.unit.save()
        super().save(*args, **kwargs)

    def update_status(self):
        if self.status == 'cancelled': 
            return
        today = timezone.now().date()
        if self.end_date < today: 
            self.status = 'expired'
        elif self.end_date - relativedelta(months=1) <= today: 
            self.status = 'expiring_soon'
        else: 
            self.status = 'active'
            
    def get_status_color(self):
        if self.status == 'active': return 'active'
        if self.status == 'expiring_soon': return 'expiring'
        if self.status == 'expired': return 'expired'
        return 'cancelled'
        
    def get_absolute_url(self):
        return reverse('lease_detail', kwargs={'pk': self.pk})

    def get_payment_summary(self):
        summary = []
        payments = self.payments.all().order_by('payment_for_year', 'payment_for_month')
        current_date = self.start_date
        while current_date <= self.end_date:
            year, month = current_date.year, current_date.month
            paid_for_month = payments.filter(payment_for_year=year, payment_for_month=month).aggregate(total=Sum('amount'))['total'] or 0
            balance = self.monthly_rent - paid_for_month
            status = 'due'
            if paid_for_month >= self.monthly_rent:
                status = 'paid'
            elif paid_for_month > 0:
                status = 'partial'
            today = timezone.now().date()
            if current_date.year > today.year or (current_date.year == today.year and current_date.month > today.month):
                status = 'upcoming'
            summary.append({
                'month': month,
                'year': year,
                'month_name': _(current_date.strftime('%B')),
                'rent_due': self.monthly_rent,
                'amount_paid': paid_for_month,
                'balance': balance,
                'status': status
            })
            current_date += relativedelta(months=1)
        return summary

    def get_absolute_url(self):
        return reverse('lease_detail', kwargs={'pk': self.pk})

    def __str__(self):
        return f"{self.contract_number} - {self.tenant.name}"

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', _('نقدي')), 
        ('bank_transfer', _('تحويل بنكي')), 
        ('cheque', _('شيك')), 
        ('online', _('دفع إلكتروني')),
    ]
    lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name='payments', verbose_name=_("العقد"))
    voucher_number = models.CharField(_("رقم سند القبض"), max_length=50, unique=True, editable=False)
    payment_date = models.DateField(_("تاريخ الدفع"))
    amount = models.DecimalField(_("المبلغ المدفوع"), max_digits=10, decimal_places=2)
    payment_method = models.CharField(_("طريقة الدفع"), max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    cheque_details = models.CharField(_("تفاصيل الشيك/التحويل"), max_length=150, blank=True, null=True, help_text=_("يُملأ فقط في حال كانت طريقة الدفع شيك"))
    payment_for_month = models.IntegerField(_("دفعة عن شهر"), choices=[(i, _(str(i))) for i in range(1, 13)])
    payment_for_year = models.IntegerField(_("دفعة عن سنة"), default=timezone.now().year)
    notes = models.TextField(_("ملاحظات"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("سند قبض (دفعة إيجار)")
        verbose_name_plural = _("سندات القبض (دفعات الإيجار)")
        ordering = ['-payment_date']
        unique_together = ('lease', 'payment_for_month', 'payment_for_year')

    def save(self, *args, **kwargs):
        if not self.voucher_number:
            self.voucher_number = get_next_voucher_number('RCPT')
        super().save(*args, **kwargs)
        
        
    def __str__(self):
        return f"{self.voucher_number} - {self.amount}"
        
class MaintenanceRequest(models.Model):
    STATUS_CHOICES = [('submitted', _('تم الإرسال')), ('in_progress', _('قيد التنفيذ')), ('completed', _('مكتمل')), ('cancelled', _('ملغي'))]
    PRIORITY_CHOICES = [('low', _('منخفضة')), ('medium', _('متوسطة')), ('high', _('عالية'))]
    lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name='maintenance_requests', verbose_name=_("العقد"))
    title = models.CharField(_("عنوان الطلب"), max_length=200)
    description = models.TextField(_("وصف المشكلة"))
    priority = models.CharField(_("الأولوية"), max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(_("الحالة"), max_length=20, choices=STATUS_CHOICES, default='submitted')
    image = models.ImageField(_("صورة مرفقة (اختياري)"), upload_to='maintenance_requests/', blank=True, null=True)
    reported_date = models.DateTimeField(_("تاريخ الإبلاغ"), auto_now_add=True)
    staff_notes = models.TextField(_("ملاحظات الموظف"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("طلب صيانة")
        verbose_name_plural = _("طلبات الصيانة")
        ordering = ['-reported_date']
        
    def __str__(self):
        return self.title

class Document(models.Model):
    lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name='documents', verbose_name=_("العقد"))
    title = models.CharField(_("عنوان المستند"), max_length=200)
    file = models.FileField(_("الملف"), upload_to='lease_documents/')
    uploaded_at = models.DateTimeField(_("تاريخ الرفع"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("مستند")
        verbose_name_plural = _("المستندات")
        ordering = ['-uploaded_at']
        
    def __str__(self):
        return self.title

class Expense(models.Model):
    EXPENSE_CATEGORY_CHOICES = [('maintenance', _('صيانة')), ('utilities', _('خدمات (كهرباء، ماء)')), ('salaries', _('رواتب')), ('marketing', _('تسويق')), ('admin', _('رسوم إدارية/حكومية')), ('other', _('أخرى'))]
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='expenses', verbose_name=_("المبنى"))
    voucher_number = models.CharField(_("رقم سند الصرف"), max_length=50, unique=True, editable=False)
    paid_to = models.CharField(_("مدفوع إلى / المستفيد"), max_length=150)
    category = models.CharField(_("فئة المصروف"), max_length=50, choices=EXPENSE_CATEGORY_CHOICES)
    description = models.CharField(_("الوصف"), max_length=255)
    amount = models.DecimalField(_("المبلغ"), max_digits=10, decimal_places=2)
    expense_date = models.DateField(_("تاريخ المصروف"))
    receipt = models.FileField(_("إيصال/فاتورة (اختياري)"), upload_to='expense_receipts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("سند صرف (مصروف)")
        verbose_name_plural = _("سندات الصرف (المصروفات)")
        ordering = ['-expense_date']

    def save(self, *args, **kwargs):
        if not self.voucher_number:
            self.voucher_number = get_next_voucher_number('PV')
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.voucher_number} - {self.description}"
        
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name=_("المستخدم"))
    message = models.TextField(_("الرسالة"))
    read = models.BooleanField(_("مقروءة"), default=False)
    timestamp = models.DateTimeField(_("الوقت"), auto_now_add=True)
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications', verbose_name=_("مرسل من"))

    class Meta:
        verbose_name = _("إشعار")
        verbose_name_plural = _("الإشعارات")
        ordering = ['-timestamp']

    def __str__(self):
        return self.message

class ContractTemplate(models.Model):
    title = models.CharField(_("عنوان القالب"), max_length=200, help_text=_("مثال: عقد إيجار شقة"))
    body = models.TextField(_("محتوى القالب"), help_text=_("استخدم المتغيرات التالية ليتم استبداله تلقائيا: {{tenant_name}}, {{ unit_full_address }}, {{ start_date }}, {{ end_date }}, {{ monthly_rent_amount }}, {{ monthly_rent_words }}, {{ contract_number }}."))

    class Meta:
        verbose_name = _("قالب عقد")
        verbose_name_plural = _("قوالب العقود")

    def __str__(self):
        return self.title