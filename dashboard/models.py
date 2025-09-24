from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal
from django.db.models import Sum

class CompanyProfile(models.Model):
    name = models.CharField(_("اسم الشركة"), max_length=200)
    logo = models.ImageField(_("شعار الشركة"), upload_to='company_logos/', blank=True, null=True)
    commercial_registration = models.CharField(_("رقم السجل التجاري"), max_length=100, blank=True)
    phone = models.CharField(_("رقم الهاتف"), max_length=20, blank=True)
    email = models.EmailField(_("البريد الإلكتروني"), blank=True)
    address = models.TextField(_("العنوان"), blank=True)

    class Meta:
        verbose_name = _("ملف الشركة")
        verbose_name_plural = _("ملفات الشركة")

    def __str__(self):
        return self.name

class Building(models.Model):
    name = models.CharField(_("اسم المبنى"), max_length=100)
    address = models.TextField(_("العنوان"))
    class Meta:
        verbose_name = _("مبنى")
        verbose_name_plural = _("المباني")
    def __str__(self):
        return self.name

class Unit(models.Model):
    UNIT_STATUS_CHOICES = [('available', _('متاحة')), ('rented', _('موجرة')), ('maintenance', _('تحت الصيانة'))]
    UNIT_TYPE_CHOICES = [('office', _('مكتب')), ('apartment', _('شقة')), ('shop', _('محل'))]
    building = models.ForeignKey(Building, on_delete=models.CASCADE, verbose_name=_("المبنى"))
    unit_number = models.CharField(_("رقم الوحدة"), max_length=20)
    unit_type = models.CharField(_("نوع الوحدة"), max_length=20, choices=UNIT_TYPE_CHOICES)
    floor = models.IntegerField(_("الطابق"))
    is_available = models.BooleanField(_("متاحة للإيجار"), default=True)
    area = models.DecimalField(_("المساحة(متر مربع)"), max_digits=8, decimal_places=2, blank=True, null=True)
    amenties = models.TextField(_("المرافق والمميزات"), blank=True, help_text=_("مفصولة بفاصلة، مثال: مكيف، واي فاي، غسالة، إلخ."))
    status = models.CharField(_("حالة الوحدة"), max_length=20, choices=UNIT_STATUS_CHOICES, default='available')
    notes = models.TextField(_("ملاحظات إدارية"), blank=True, help_text=_("ملاحظات خاصة بالموظفين، غير مرئية للمستأجرين."))
    class Meta:
        verbose_name = _("وحدة")
        verbose_name_plural = _("الوحدات")
    def __str__(self):
        return f"{self.building.name} - {self.unit_number}"

class UnitImage(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='images', verbose_name=_("الوحدة"))
    image = models.ImageField(_("صورة الوحدة"), upload_to='unit_images/')

    class Meta:
        verbose_name = _("صورة الوحدة")
        verbose_name_plural = _("صور الوحدات")

    def __str__(self):
        return f"Image for {self.unit}"

class Tenant(models.Model):
    TENANT_TYPE_CHOICES = [('individual', _('فرد')), ('company', _('شركة'))]
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("حساب المستخدم"), help_text=_("اربط المستأجر بحساب مستخدم لتسجيل الدخول إلى البوابة."))
    name = models.CharField(_("اسم المستأجر"), max_length=150)
    tenant_type = models.CharField(_("نوع المستأجر"), max_length=20, choices=TENANT_TYPE_CHOICES)
    phone = models.CharField(_("رقم الهاتف"), max_length=15)
    email = models.EmailField(_("البريد الإلكتروني"), blank=True, null=True)
    authorized_signatory = models.CharField(_("المفوض بالتوقيع"), max_length=150, blank=True, null=True, help_text=_("يُملأ فقط في حال كان المستأجر شركة"))
    class Meta:
        verbose_name = _("مستأجر")
        verbose_name_plural = _("المستأجرين")
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
    class Meta:
        verbose_name = _("عقد إيجار")
        verbose_name_plural = _("عقود الإيجار")
    def save(self, *args, **kwargs):
        self.registration_fee = (self.monthly_rent * 12) * Decimal('0.03')
        self.update_status()
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
        today = timezone.now().date()
        if self.status == 'cancelled': return
        if self.end_date < today: self.status = 'expired'
        elif self.end_date - relativedelta(months=1) <= today: self.status = 'expiring_soon'
        else: self.status = 'active'
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
    lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name='payments', verbose_name=_("العقد"))
    payment_date = models.DateField(_("تاريخ الدفع"))
    amount = models.DecimalField(_("المبلغ المدفوع"), max_digits=10, decimal_places=2)
    payment_for_month = models.IntegerField(_("دفعة عن شهر"), choices=[(i, _(str(i))) for i in range(1, 13)])
    payment_for_year = models.IntegerField(_("دفعة عن سنة"), default=timezone.now().year)
    notes = models.TextField(_("ملاحظات"), blank=True, null=True)
    class Meta:
        verbose_name = _("دفعة")
        verbose_name_plural = _("الدفعات")
        ordering = ['-payment_date']
        unique_together = ('lease', 'payment_for_month', 'payment_for_year')
    def __str__(self):
        return f"{self.amount} for {self.lease.contract_number} ({self.payment_for_month}/{self.payment_for_year})"

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
    category = models.CharField(_("فئة المصروف"), max_length=50, choices=EXPENSE_CATEGORY_CHOICES)
    description = models.CharField(_("الوصف"), max_length=255)
    amount = models.DecimalField(_("المبلغ"), max_digits=10, decimal_places=2)
    expense_date = models.DateField(_("تاريخ المصروف"))
    receipt = models.FileField(_("إيصال/فاتورة (اختياري)"), upload_to='expense_receipts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = _("مصروف")
        verbose_name_plural = _("المصاريف")
        ordering = ['-expense_date']
    def __str__(self):
        return f"{self.get_category_display()} - {self.amount}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name=_("المستخدم"))
    message = models.TextField(_("الرسالة"))
    read = models.BooleanField(_("مقروءة"), default=False)
    timestamp = models.DateTimeField(_("الوقت"), auto_now_add=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = _("إشعار")
        verbose_name_plural = _("الإشعارات")
        ordering = ['-timestamp']

    def __str__(self):
        return self.message