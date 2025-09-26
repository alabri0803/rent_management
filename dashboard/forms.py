from django import forms
from .models import Lease, Unit, MaintenanceRequest, Document, Expense, Payment, Tenant, Notification, ContractTemplate
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class LeaseForm(forms.ModelForm):
    class Meta:
        model = Lease
        fields = ['unit', 'tenant', 'template', 'contract_number', 'contract_form_number', 'monthly_rent', 'start_date', 'end_date', 'electricity_meter', 'water_meter', 'office_fee', 'admin_fee']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}), 
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show only available units, or the currently selected one if editing
        if self.instance and self.instance.pk:
            self.fields['unit'].queryset = Unit.objects.filter(is_available=True) | Unit.objects.filter(pk=self.instance.unit.pk)
        else:
            self.fields['unit'].queryset = Unit.objects.filter(is_available=True)

        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-[#993333]'})

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
        fields = ['building', 'category', 'description', 'amount', 'expense_date', 'receipt', 'paid_to']
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
        fields = ['lease', 'payment_date', 'amount', 'payment_for_month', 'cheque_details', 'payment_method', 'notes', 'payment_for_year']
        widgets = {'payment_date': forms.DateInput(attrs={'type': 'date'})}
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_for_year'].initial = timezone.now().year
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full p-2 border rounded-md'})

class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['rating', 'internal_notes']
        widgets = {'internal_notes': forms.Textarea(attrs={'rows': 4})}
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-[#993333]'})

class SendMessageForm(forms.Form):
    class Meta:
        model = Notification
        fields = ['message']
        widgets = {'message': forms.Textarea(attrs={'rows': 3, 'placeholder': _('اكتب رسالتك هنا...')})}
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['message'].label = _("رسالة جديدة")
        self.fields['message'].widget.attrs.update({'class': 'w-full p-2 border rounded-md'})

class LeaseCancellationForm(forms.ModelForm):
    class Meta:
        model = Lease
        fields = ['cancellation_date', 'cancellation_reason']
        widgets = {
            'cancellation_date': forms.DateInput(attrs={'type': 'date', 'required': True}),
            'cancellation_reason': forms.Textarea(attrs={'rows': 4, 'required': True}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cancellation_date'].initial = timezone.now().date()
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-[#993333]'})