from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

class CustomUserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    ROLE_CHOICES = (
        ('staff', _('موظف / مشرف')),
        ('tenant', _('مستأجر')),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True, label=_("الدور"))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'role']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        role = self.cleaned_data["role"]
        if role == 'staff':
            user.is_staff = True
        if commit:
            user.save()
        return user