from modeltranslation.translator import register, TranslationOptions
from .models import Building, Tenant, MaintenanceRequest, Expense

@register(Building)
class BuildingTranslationOptions(TranslationOptions):
    fields = ('name', 'address')

@register(Tenant)
class TenantTranslationOptions(TranslationOptions):
    fields = ('name', 'authorized_signatory')

@register(MaintenanceRequest)
class MaintenanceRequestTranslationOptions(TranslationOptions):
    fields = ('title', 'description', 'staff_notes')

@register(Expense)
class ExpenseTranslationOptions(TranslationOptions):
    fields = ('description',)