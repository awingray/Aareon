from django import forms
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


class BaseComponentForm(forms.ModelForm):
    """A form for the user to set the fields of a base component.  Tenancy is added automatically."""
    class Meta:
        model = models.BaseComponent
        exclude = ['tenancy']