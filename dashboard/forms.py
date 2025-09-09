from django import forms
from .models import Lease, Unit, MaintenanceRequest, Document

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

class MaintenanceRequestForm(forms.ModelForm):
  class Meta:
    model = MaintenanceRequest
    fields = ['title', 'description', 'priority', 'image']
    widgets = {
      'description': forms.Textarea(attrs={'rows': 4}),
    }

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    for field_name, field in self.fields.items():
      field.widget.attrs.update({'class':'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-[#993333]'})

class MaintenanceRequestUpdateForm(forms.ModelForm):
  class Meta:
    model = MaintenanceRequest
    fields = ['status', 'staff_notes']

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    for field_name, field in self.fields.items():
      field.widget.attrs.update({'class':'w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-[#993333]'})

class DocumentForm(forms.ModelForm):
  class Meta:
    model = Document
    fields = ['title', 'file']

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['file'].widget.attrs.update({'class':'w-full text-sm text-gray-500 file:px-4 file:mr-4 file:py-2 file:border-0 file:text-sm file:font-semibold file:bg-bule-50 file:text-bule-700 hover:file:bg-bule-100'})