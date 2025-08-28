from django import forms
from .models import Lease, Tenant, Unit
from django.utils.translation import gettext_lazy as _

class LeaseForm(forms.ModelForm):
  class Meta:
    model = Lease
    fields = ['unit', 'tenant', 'contract_number', 'contract_form_number', 'monthly_rent', 'start_date', 'end_date', 'electricity_meter', 'water_meter', 'office_fee', 'admin_fee']
    widgets = {
      'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
      'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
      'unit': forms.Select(attrs={'class': 'form-select'}),
      'tenant': forms.Select(attrs={'class': 'form-select'}),
    }

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['unit'].queryset = Unit.objects.filter(is_available=True)
    for field_name, field in self.fields.items():
      field.widget.attrs.update({'class':'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-[#993333]'})