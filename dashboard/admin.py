from django.contrib import admin
from .models import Building, Unit, Tenant, Lease, Payment, MaintenanceRequest, Document, Expense, Notification, CompanyProfile, UnitImage
from django.utils.translation import gettext_lazy as _

# تخصيص عرض المباني والوحدات
@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('name', 'address')
    search_fields = ('name',)

class UnitImageInline(admin.TabularInline):
    model = UnitImage
    extra = 1
    fields = ('image', 'caption')

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('unit_number', 'building', 'unit_type', 'status', 'area', 'is_available')
    list_filter = ('building', 'unit_type', 'status', 'is_available')
    search_fields = ('unit_number', 'building__name')
    fieldsets = (
        (None, {
            'fields': ('building', 'unit_number', 'unit_type', 'floor', 'status')
        }),
        (_('تفاصيل إضافية'), {
            'fields': ('area', 'amenties', 'notes'),
            'classes': ('collapse',),
        }),
    )
    inlines = [UnitImageInline]

# تخصيص عرض المستأجرين
@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
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
class ExpenseAdmin(admin.ModelAdmin):
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

@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email')
    def has_add_permission(self, request):
        return not CompanyProfile.objects.count() == 0