from django import forms
from .models import models


class TenancyForm(forms.ModelForm):
    class Meta:
        model = models.Tenancy
        fields = "__all__"
