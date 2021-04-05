from django import forms
from django.shortcuts import get_object_or_404

from InvoiceEngineApp import models


class TenancyForm(forms.ModelForm):
    """A form for the user to set the name and the date for the next prolonging for a tenancy.
    All other fields are derived and should not be changed by users.
    """
    class Meta:
        model = models.Tenancy
        exclude = ['tenancy_id', 'number_of_contracts', 'last_invoice_number']


class ContractTypeForm(forms.ModelForm):
    """A form for the user to set the fields of a contract type.  Tenancy is added automatically."""
    def finalize_creation(self, view_object):
        self.instance.tenancy = view_object.tenancy

    class Meta:
        model = models.ContractType
        exclude = ['tenancy']


class BaseComponentForm(forms.ModelForm):
    """A form for the user to set the fields of a base component.  Tenancy is added automatically."""
    def finalize_creation(self, view_object):
        self.instance.tenancy = view_object.tenancy

    class Meta:
        model = models.BaseComponent
        exclude = ['tenancy']


class VATRateForm(forms.ModelForm):
    """A form for the user to set the fields of a VAT rate.  Tenancy is added automatically."""
    def finalize_creation(self, view_object):
        self.instance.tenancy = view_object.tenancy

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if end_date and end_date < start_date:
            raise forms.ValidationError("End date should be greater than start date.")

    class Meta:
        model = models.VATRate
        exclude = ['tenancy']


class ContractForm(forms.ModelForm):
    """A form for the user to set the fields of a contract.  Tenancy is added automatically.
    The user can choose contract type from a drop-down menu.
    """
    def filter_selectors(self, tenancy):
        self.fields['contract_type'].queryset = models.ContractType.objects.filter(tenancy=tenancy)

    def finalize_creation(self, view_object):
        self.instance.tenancy = view_object.tenancy

        self.instance.tenancy.number_of_contracts += 1
        self.instance.tenancy.clean()
        self.instance.tenancy.save()

    class Meta:
        model = models.Contract
        exclude = ['tenancy', 'invoicing_amount_type', 'balance', 'base_amount', 'vat_amount', 'total_amount']


class ComponentForm(forms.ModelForm):
    """A form for the user to set the fields of a component."""
    def filter_selectors(self, tenancy):
        self.fields['base_component'].queryset = models.BaseComponent.objects.filter(tenancy=tenancy)
        self.fields['vat_rate'].queryset = models.VATRate.objects.filter(tenancy=tenancy)

    def finalize_creation(self, view_object):
        self.instance.tenancy = view_object.tenancy
        self.instance.contract = get_object_or_404(
            models.Contract,
            contract_id=view_object.kwargs.get('contract_id')
        )
        self.finalize_update()

    def finalize_update(self):
        self.instance.vat_amount = self.instance.base_amount * self.instance.vat_rate.percentage / 100
        self.instance.total_amount = self.instance.base_amount + self.instance.vat_amount

    class Meta:
        model = models.Component
        exclude = ['contract', 'vat_amount', 'total_amount', 'tenancy']


class ContractPersonForm(forms.ModelForm):
    """A form for the user to set the fields of a contract person."""
    def finalize_creation(self, view_object):
        self.instance.tenancy = view_object.tenancy
        self.instance.contract = get_object_or_404(
            models.Contract,
            contract_id=view_object.kwargs.get('contract_id')
        )

    class Meta:
        model = models.ContractPerson
        exclude = ['contract', 'tenancy']
