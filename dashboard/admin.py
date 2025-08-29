from django.contrib import admin
from .models import Building, Unit, Tenant, Lease, Payment
from django.utils.translation import gettext_lazy as _

admin.site.site_header = _('لوحة تحكم نظام إدارة الإيجارات')
admin.site.site_title = _('إدارة الإيجارات')
admin.site.index_title = _('مرحبًا بك في لوحة التحكم')

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1
    readonly_fields = ('payment_date',)
    fields = ('payment_date', 'amount', 'notes')
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.pk:
            return ['payment_date', 'amount', 'notes']
        return []

@admin.register(Lease)
class LeaseAdmin(admin.ModelAdmin):
    list_display = ('contract_number', 'tenant', 'unit', 'end_date', 'status')
    list_filter = ('status', 'unit__building')
    search_fields = ('contract_number', 'tenant__name', 'unit__unit_number')
    readonly_fields = ('registration_fee', 'status')
    fieldsets = (
        (_('المعلومات الأساسية'), {
            'fields': ('contract_number', 'contract_form_number', 'tenant', 'unit')
            }),
        (_('التواريخ والمدة'), {
            'fields': ('start_date', 'end_date')
        }),
        (_('المعلومات المالية'), {
            'fields': ('monthly_rent', 'office_fee', 'admin_fee', 'registration_fee')
        }),
        (_('بيانات العدادات'), {
            'fields': ('electricity_meter', 'water_meter')
        }),
        (_('الحالة'), {
            'fields': ('status',)
        }),
    )
    inlines = [PaymentInline]
    def save_model(self, request, obj, form, change):
        if not change:
            obj.unit.is_available = False
            obj.unit.save()
        super().save_model(request, obj, form, change)

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant_type', 'phone', 'user_link')
    search_fields = ('name', 'phone', 'email')
    list_filter = ('tenant_type',)
    def user_link(self, obj):
      if obj.user:
        return _("غير مربوط")
    user_link.short_description = _('حساب المستخدم')

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('unit_number', 'building', 'unit_type', 'floor', 'is_available')
    list_filter = ('is_available', 'unit_type', 'building')
    search_fields = ('unit_number', 'building__name')
    list_editable = ('is_available',)

@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('name', 'address')
    search_fields = ('name',)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('lease', 'payment_date', 'amount')
    list_filter = ('lease__unit__building',)
    search_fields = ('lease__contract_number',)
    autocomplete_fields = ('lease',)