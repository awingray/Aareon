from django import forms
from django.shortcuts import get_object_or_404

from InvoiceEngineApp import models


class TenancyFrom(forms.ModelForm):
    """A form for the user to set the name and the date for the next prolonging for a tenancy.
    All other fields are derived and should not be changed by users.
    """
    class Meta:
        model = models.Tenancy
        exclude = ['tenancy_id', 'number_of_contracts', 'last_invoice_number']


class ContractTypeForm(forms.ModelForm):
    """A form for the user to set the fields of a contract type.  Tenancy is added automatically."""
    class Meta:
        model = models.ContractType
        exclude = ['tenancy']

    def set_tenancy(self, company_id):
        self.instance.tenancy = get_object_or_404(models.Tenancy, company_id=company_id)


class BaseComponentForm(forms.ModelForm):
    """A form for the user to set the fields of a base component.  Tenancy is added automatically."""
    class Meta:
        model = models.BaseComponent
        exclude = ['tenancy']

    def set_tenancy(self, company_id):
        self.instance.tenancy = get_object_or_404(models.Tenancy, company_id=company_id)


class VATRateForm(forms.ModelForm):
    """A form for the user to set the fields of a VAT rate.  Tenancy is added automatically."""
    class Meta:
        model = models.VATRate
        exclude = ['tenancy']

    def set_tenancy(self, company_id):
        self.instance.tenancy = get_object_or_404(models.Tenancy, company_id=company_id)

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if end_date < start_date:
            raise forms.ValidationError("End date should be greater than start date.")
