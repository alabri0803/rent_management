from django import forms
from .models import Lease, Unit, MaintenanceRequest, Document, Expense, Payment, Company, Tenant, Building
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

# ADDED
class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'logo', 'contact_email', 'contact_phone', 'address']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-[#993333]'})

class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['building', 'unit_number', 'unit_type', 'floor', 'is_available']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-[#993333]'})

class BuildingForm(forms.ModelForm):
    class Meta:
        model = Building
        fields = ['name', 'address']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-[#993333]'})

class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['name', 'tenant_type', 'phone', 'email', 'authorized_signatory', 'rating']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-[#993333]'})


class LeaseForm(forms.ModelForm):
    class Meta:
        model = Lease
        fields = ['unit', 'tenant', 'contract_number', 'contract_form_number', 'monthly_rent', 'start_date', 'end_date', 'electricity_meter', 'water_meter', 'office_fee', 'admin_fee']
        widgets = {'start_date': forms.DateInput(attrs={'type': 'date'}), 'end_date': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['unit'].queryset = Unit.objects.filter(is_available=True) | Unit.objects.filter(pk=self.instance.unit.pk)
        else:
            self.fields['unit'].queryset = Unit.objects.filter(is_available=True)

        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-[#993333]'})

# ADDED
class LeaseCancelForm(forms.ModelForm):
    class Meta:
        model = Lease
        fields = ['cancellation_reason']
        widgets = {
            'cancellation_reason': forms.Textarea(attrs={'rows': 4, 'placeholder': _('يرجى ذكر سبب إلغاء العقد...')})
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full p-2 border rounded-md'})

# ADDED
class TenantRatingForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['rating']
        widgets = {
            'rating': forms.Select(attrs={'class': 'p-2 border rounded-md'})
        }

class MaintenanceRequestForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ['title', 'description', 'priority', 'image']
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-[#993333]'})

class MaintenanceRequestUpdateForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ['status', 'staff_notes']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-[#993333]'})

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'file']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update({'class': 'w-full p-2 border rounded-md', 'placeholder': _('مثال: نسخة من العقد الموقّع')})
        self.fields['file'].widget.attrs.update({'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'})

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['building', 'category', 'description', 'amount', 'expense_date', 'receipt']
        widgets = {'expense_date': forms.DateInput(attrs={'type': 'date'})}
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            common_class = 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-[#993333]'
            if field_name == 'receipt':
                field.widget.attrs.update({'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'})
            else:
                field.widget.attrs.update({'class': common_class})

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['lease', 'payment_date', 'amount', 'payment_for_month', 'payment_for_year', 'payment_method', 'check_number', 'check_date', 'bank_name', 'check_status', 'return_reason', 'notes']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'check_date': forms.DateInput(attrs={'type': 'date'})
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_for_year'].initial = timezone.now().year
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full p-2 border rounded-md'})
    
    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        check_status = cleaned_data.get('check_status')
        return_reason = cleaned_data.get('return_reason')
        
        if payment_method == 'check':
            if not check_status:
                self.add_error('check_status', _('حالة الشيك مطلوبة عند اختيار طريقة الدفع بالشيك'))
            
            if check_status == 'returned' and not return_reason:
                self.add_error('return_reason', _('سبب إرجاع الشيك مطلوب عند اختيار حالة "مرتجع"'))
        
        return cleaned_data