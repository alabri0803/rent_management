from modeltranslation.translator import register, TranslationOptions
from .models import Building, Unit, Tenant, Expense

@register(Building)
class BuildingTranslationOptions(TranslationOptions):
    fields = ('name', 'address')

@register(Unit)
class UnitTranslationOptions(TranslationOptions):
    fields = ()

@register(Tenant)
class TenantTranslationOptions(TranslationOptions):
    fields = ('name', 'authorized_signatory')

@register(Expense)
class ExpenseTranslationOptions(TranslationOptions):
    fields = ('description',)