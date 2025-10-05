from modeltranslation.translator import translator, TranslationOptions
from .models import Building, Tenant, Expense


class BuildingTranslationOptions(TranslationOptions):
    fields = ('name', 'address')


class TenantTranslationOptions(TranslationOptions):
    fields = ('name', 'authorized_signatory')


class ExpenseTranslationOptions(TranslationOptions):
    fields = ('description',)


translator.register(Building, BuildingTranslationOptions)
translator.register(Tenant, TenantTranslationOptions)
translator.register(Expense, ExpenseTranslationOptions)
