from django.contrib import admin
from .models import CompanyProfile, Building, Unit, Tenant, Lease, Payment, MaintenanceRequest, Document, Expense, Notification
from modeltranslation.admin import TabbedTranslationAdmin
from solo.admin import SingletonModelAdmin

@admin.register(CompanyProfile)
class CompanyProfileAdmin(SingletonModelAdmin):
    pass

# تخصيص عرض المباني والوحدات
@admin.register(Building)
class BuildingAdmin(TabbedTranslationAdmin):
    list_display = ('name', 'address')
    search_fields = ('name',)

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('unit_number', 'building', 'unit_type', 'floor', 'is_available')
    list_filter = ('building', 'unit_type', 'is_available')
    search_fields = ('unit_number', 'building__name')

# تخصيص عرض المستأجرين
@admin.register(Tenant)
class TenantAdmin(TabbedTranslationAdmin):
    list_display = ('name', 'tenant_type', 'phone', 'email', 'user')
    list_filter = ('tenant_type',)
    search_fields = ('name', 'phone', 'email')

# تخصيص عرض العقود
@admin.register(Lease)
class LeaseAdmin(admin.ModelAdmin):
    list_display = ('contract_number', 'tenant', 'unit', 'start_date', 'end_date', 'monthly_rent', 'status')
    list_filter = ('status', 'unit__building')
    search_fields = ('contract_number', 'tenant__name', 'unit__unit_number')
    date_hierarchy = 'start_date'

# تخصيص عرض المدفوعات
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('lease', 'payment_date', 'amount', 'payment_for_month', 'payment_for_year')
    list_filter = ('payment_for_year',)
    search_fields = ('lease__contract_number', 'lease__tenant__name')
    date_hierarchy = 'payment_date'

# تخصيص عرض طلبات الصيانة
@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'lease', 'priority', 'status', 'reported_date')
    list_filter = ('status', 'priority')
    search_fields = ('title', 'lease__contract_number')

# تخصيص عرض المصاريف
@admin.register(Expense)
class ExpenseAdmin(TabbedTranslationAdmin):
    list_display = ('description', 'building', 'category', 'amount', 'expense_date')
    list_filter = ('category', 'building')
    search_fields = ('description',)
    date_hierarchy = 'expense_date'

# تسجيل نموذج المستندات (عرض افتراضي)
admin.site.register(Document)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'read', 'timestamp')
    list_filter = ('read', 'user')