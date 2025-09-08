from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.urls import reverse
from django.contrib.auth.models import User

# السجل التجاري
class Building(models.Model):
  name = models.CharField(_('اسم المبني'), max_length=100)
  address = models.TextField(_('العنوان'))

  class Meta:
    verbose_name = _('مبني')
    verbose_name_plural = _('المباني')

  def __str__(self):
    return self.name

# الوحدات داخل المبني (شقق، مكاتب، محلات)
class Unit(models.Model):
  UNIT_TYPE_CHOICES = [
    ('Office', _('مكتب')),
    ('Apartment', _('شقة')),
    ('shop', _('محل')),
  ]
  building = models.ForeignKey(Building, on_delete=models.CASCADE, verbose_name=_('المبني'))
  unit_number = models.CharField(_('رقم الوحدة'), max_length=20)
  unit_type = models.CharField(_('نوع الوحدة'), max_length=20, choices=UNIT_TYPE_CHOICES)
  floor = models.IntegerField(_('الطابق'))
  is_available = models.BooleanField(_('متاحة الإيجار'), default=True)

  class Meta:
    verbose_name = _('وحدة')
    verbose_name_plural = _('الوحدات')

  def __str__(self):
    return f"{self.building.name} - {self.unit_number}"

# المستأجر
class Tenant(models.Model):
  TENANT_TYPE_CHOICES = [
    ('Individual', _('فرد')),
    ('Company', _('شركة')),
  ]
  user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('حساب المستخدم'), help_text=_('اربط المستأجر بحساب مستخدم لتسجيل الدخول إلى البوابة'))
  name = models.CharField(_('اسم المستأجر'), max_length=150)
  tenant_type = models.CharField(_('نوع المستأجر'), max_length=20, choices=TENANT_TYPE_CHOICES)
  phone = models.CharField(_('رقم الهاتف'), max_length=15)
  email = models.EmailField(_('البريد الإلكتروني'), blank=True, null=True)
  authorized_signatory = models.CharField(_('المفوض بالتوقيع'), max_length=150, blank=True, null=True, help_text=_('يملا فقط في حال كان المستأجر شركة'))

  class Meta:
    verbose_name = _('مستأجر')
    verbose_name_plural = _('المستأجرين')

  def __str__(self):
    return self.name
    
# عقود الإيجار
class Lease(models.Model):
  STATUS_CHOICES = [
    ('active', _('نشط')),
    ('expired_soon', _('قريب الانتهاء')),
    ('expired', _('منتهي')),
    ('canceled', _('ملغي')),
  ]
  unit = models.ForeignKey(Unit, on_delete=models.CASCADE, verbose_name=_('الوحدة'))
  tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, verbose_name=_('المستأجر'))
  contract_number = models.CharField(_('رقم العقد'), max_length=50, unique=True)
  contract_form_number = models.CharField(_('رقم نموذج العقد'), max_length=50, blank=True, null=True)
  monthly_rent = models.DecimalField(_('مبلغ الإيجار الشهري'), max_digits=10, decimal_places=2)
  start_date = models.DateField(_('تاريخ بدء العقد'))
  end_date = models.DateField(_('تاريخ انتهاء العقد'))
  electricity_meter = models.CharField(_('رقم عداد الكهرباء'), max_length=50, blank=True, null=True)
  water_meter = models.CharField(_('رقم عداد الماء'), max_length=50, blank=True, null=True)
  status = models.CharField(_('حالة العقد'), max_length=20, choices=STATUS_CHOICES, default='active')

  # الرسوم المحسوبة
  office_fee = models.DecimalField(_('رسوم المكتب'), max_digits=10, decimal_places=2, default=5.00)
  admin_fee = models.DecimalField(_('الرسوم الإدارة'), max_digits=10, decimal_places=2, default=1.00)
  registration_fee = models.DecimalField(_('رسوم تسجيل العقد (٣٪؜)'), max_digits=10, decimal_places=2, blank=True)

  class Meta:
    verbose_name = _('عقد إيجار')
    verbose_name_plural = _('عقود الإيجار')

  def save(self, *args, **kwargs):
    # حساب رسوم التسجيل تقائيا عند الحفظ
    self.registration_fee = (self.monthly_rent * 12) * 0.03
    super().save(*args, **kwargs)

  def update_status(self):
    today = timezone.now().date()
    if self.status == 'canceled':
      return 
    if self.end_date < today:
      self.status = 'expired'
    elif self.end_date - relativedelta(months=1) <= today:
      self.status = 'expired_soon'
    else:
      self.status = 'active'
      
  def get_status_color(self):
    if self.status == 'active':
      return 'active' # أخضر
    if self.status == 'expired_soon':
      return 'expired' # أصفر
    if self.status == 'expired':
      return 'expired' # أحمر
    return 'cancelled' # رمادي

  def get_absolute_url(self):
    return reverse('lease_detail', kwargs={'pk': self.pk})


  def __str__(self):
    return f"عقد {self.contract_number} - {self.tenant.name}"

class Payment(models.Model):
  lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name='payments', verbose_name=_('العقد'))
  payment_date = models.DateField(_('تاريخ الدفع'))
  amount = models.DecimalField(_('المبلغ المدفوع'), max_digits=10, decimal_places=2)
  notes = models.TextField(_('ملاحظات'), blank=True, null=True)

  class Meta:
    verbose_name = _('دفعة')
    verbose_name_plural = _('الدفعات')
    ordering = ['-payment_date']

    def __str__(self):
      return f"دفعة بقيمة {self.amount} للعقد {self.lease.contract_number}"

class MaintenanceRequest(models.Model):
  STATUS_CHOICES = [
    ('submitted', _('تم الإرسال')),
    ('in_progress', _('قيد التنفيذ')),
    ('completed', _('مكتمل')),
    ('canceled', _('ملغي')),
  ]
  PRIORITY_CHOICES = [
    ('low', _('منخفضة')),
    ('medium', _('متوسطة')),
    ('high', _('عالية')),
  ]
  lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name='maintenance_requests', verbose_name=_('العقد'))
  title = models.CharField(_('عنوان الطلب'), max_length=200)
  description = models.TextField(_('وصف المشكلة'))
  priority = models.CharField(_('الأولوية'), max_length=10, choices=PRIORITY_CHOICES, default='medium')
  status = models.CharField(_('الحالة'), max_length=20, choices=STATUS_CHOICES, default='submitted')
  image = models.ImageField(_('صورة مرفقة (اختياري)'), upload_to='maintenance_requests/', blank=True, null=True)
  reported_date = models.DateTimeField(_('تاريخ الإبلاغ'), auto_now_add=True)
  staff_notes = models.TextField(_('ملاحظات الموظف'), blank=True, null=True)

  class Meta:
    verbose_name = _('طلب صيانة')
    verbose_name_plural = _('طلبات الصيانة')
    ordering = ['-reported_date']

  def __str__(self):
    return self.title