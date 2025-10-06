from modeltranslation.translator import translator, TranslationOptions
from .models import Building, Tenant, Expense, Company


class BuildingTranslationOptions(TranslationOptions):
    fields = ('name', 'address')


class TenantTranslationOptions(TranslationOptions):
    fields = ('name', 'authorized_signatory')


class ExpenseTranslationOptions(TranslationOptions):
    fields = ('description',)


class CompanyTranslationOptions(TranslationOptions):
    fields = ('name', 'address')


translator.register(Building, BuildingTranslationOptions)
translator.register(Tenant, TenantTranslationOptions)
translator.register(Expense, ExpenseTranslationOptions)
translator.register(Company, CompanyTranslationOptions)
