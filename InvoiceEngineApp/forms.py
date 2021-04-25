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
            raise forms.ValidationError("End date should be after start date.")

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
        self.instance.next_date_prolong = self.instance.start_date

        self.instance.tenancy.number_of_contracts += 1
        self.instance.tenancy.clean()
        self.instance.tenancy.save()

    class Meta:
        model = models.Contract
        exclude = ['tenancy', 'invoicing_amount_type', 'next_date_prolong',
                   'balance', 'base_amount', 'vat_amount', 'total_amount'
                   ]


class ComponentForm(forms.ModelForm):
    """A form for the user to set the fields of a component."""
    def filter_selectors(self, tenancy):
        self.fields['base_component'].queryset = models.BaseComponent.objects.filter(tenancy=tenancy)
        self.fields['vat_rate'].queryset = models.VATRate.objects.filter(tenancy=tenancy)

    def clean(self):
        cleaned_data = super().clean()
        base_amount = cleaned_data.get("base_amount")
        unit_id = cleaned_data.get("base_component").unit_id
        unit_amount = cleaned_data.get("unit_amount")
        number_of_units = cleaned_data.get("number_of_units")

        # Check that using base amount or units is mutually exclusive
        if unit_id:
            if base_amount:
                raise forms.ValidationError(
                    "Please specify unit amount and number of units for unit " + unit_id.__str__()
                    + ". Do not specify base amount."
                )
            if not unit_amount or not number_of_units:
                raise forms.ValidationError(
                    "Please specify unit amount and number of units for unit " + unit_id.__str__() + "."
                )
        else:
            if not base_amount:
                raise forms.ValidationError("Please specify a base amount for this component.")
            if unit_amount or number_of_units:
                raise forms.ValidationError(
                    "Please specify a base amount for this component. Do not specify unit amount and number of units."
                )

        # Check that end date is after start date
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if end_date and end_date < start_date:
            raise forms.ValidationError("End date should be after start date.")

        # Check that end date of prolonging is after start date and before or on end date
        end_date_prolong = cleaned_data.get("end_date_prolong")
        if end_date_prolong:
            if end_date_prolong < start_date:
                raise forms.ValidationError("End date of prolonging should be after start date.")
            if end_date_prolong > end_date:
                raise forms.ValidationError("End date of prolonging should be before or on the end date.")

    def finalize_creation(self, view_object):
        self.instance.tenancy = view_object.tenancy
        contract = get_object_or_404(
            models.Contract,
            contract_id=view_object.kwargs.get('contract_id')
        )
        self.instance.contract = contract
        self.instance.next_date_prolong = contract.next_date_prolong
        self.instance.unit_id = self.instance.base_component.unit_id
        self.finalize_update()

    def finalize_update(self):
        # Base amount and unit amount are mutually exclusive.  This is handled in clean()
        amount = self.instance.base_amount
        if not amount:
            amount = self.instance.number_of_units * self.instance.unit_amount

        self.instance.vat_amount = amount * self.instance.vat_rate.percentage / 100
        self.instance.total_amount = amount + self.instance.vat_amount

        # Update contract, then save contract
        self.instance.contract.total_amount += self.instance.total_amount
        self.instance.contract.vat_amount += self.instance.vat_amount
        self.instance.contract.base_amount += amount
        self.instance.contract.save()

    class Meta:
        model = models.Component
        exclude = ['contract', 'vat_amount', 'total_amount', 'tenancy', 'next_date_prolong', 'unit_id']


class ContractPersonForm(forms.ModelForm):
    """A form for the user to set the fields of a contract person."""
    def finalize_creation(self, view_object):
        pass

    def set_dependencies(self, tenancy, contract_id):
        self.instance.tenancy = tenancy
        self.instance.contract = get_object_or_404(
            models.Contract,
            contract_id=contract_id
        )

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get("payment_method")
        iban = cleaned_data.get("iban")
        mandate = cleaned_data.get("mandate")

        if payment_method == self.instance.DIRECT_DEBIT:
            if not iban or not mandate:
                raise forms.ValidationError("Please provide an iban and a mandate.")

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if end_date and end_date < start_date:
            raise forms.ValidationError("End date should be after start date.")

        percentage = cleaned_data.get("percentage_of_total")
        db_sum_percentage = self.instance.contract.validate()
        if self.instance.percentage_of_total:
            db_sum_percentage -= self.instance.percentage_of_total

        total_percentage = db_sum_percentage + percentage
        if total_percentage > 100:
            raise forms.ValidationError(
                'Total of all persons exceeding 100% by ' + (total_percentage - 100).__str__() + '%'
            )

    class Meta:
        model = models.ContractPerson
        exclude = ['contract', 'tenancy']
