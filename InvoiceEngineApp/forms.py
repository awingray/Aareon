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


class ContractForm(forms.ModelForm):
    """A form for the user to set the fields of a contract.  Tenancy is added automatically.
    The user can choose contract type from a drop-down menu.
    """
    def __init__(self, *args, **kwargs):
        # Receive the company_id from the view, and use it to make a selection of the available contract types.
        company_id = kwargs.pop('company_id')

        super(ContractForm, self).__init__(*args, **kwargs)

        selected_tenancy = get_object_or_404(models.Tenancy, company_id=company_id)

        self.fields['contract_type'].queryset = models.ContractType.objects.filter(tenancy=selected_tenancy)

    class Meta:
        model = models.Contract
        exclude = ['tenancy', 'invoicing_amount_type', 'balance', 'base_amount', 'vat_amount', 'total_amount']

    def set_tenancy(self, company_id):
        self.instance.tenancy = get_object_or_404(models.Tenancy, company_id=company_id)


class ComponentForm(forms.ModelForm):
    """A form for the user to set the fields of a component."""
    def __init__(self, *args, **kwargs):
        # Receive the company_id from the view, and use it to make a selection of the available contracts,
        # base components, and vat rates
        company_id = kwargs.pop('company_id')

        super(ComponentForm, self).__init__(*args, **kwargs)

        selected_tenancy = get_object_or_404(models.Tenancy, company_id=company_id)

        self.fields['contract'].queryset = models.Contract.objects.filter(tenancy=selected_tenancy)
        self.fields['base_component'].queryset = models.BaseComponent.objects.filter(tenancy=selected_tenancy)
        self.fields['vat_rate'].queryset = models.VATRate.objects.filter(tenancy=selected_tenancy)

    class Meta:
        model = models.Component
        exclude = ['vat_amount', 'total_amount']
