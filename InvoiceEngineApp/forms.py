import datetime

from django import forms

from InvoiceEngineApp import models


class TenancyAdministratorForm(forms.ModelForm):
    """A form for the administrator to create a new tenancy."""
    class Meta:
        model = models.Tenancy
        exclude = [
            'number_of_contracts', 'last_invoice_number',
            'days_until_invoice_expiration', 'date_next_prolongation'
        ]


class TenancySubscriberForm(forms.ModelForm):
    """A form for the user to update a tenancy."""
    class Meta:
        model = models.Tenancy
        exclude = [
            'tenancy_id', 'name',
            'number_of_contracts', 'last_invoice_number'
        ]


class ContractTypeForm(forms.ModelForm):
    """A form for the user to set the fields of a contract type.
    Tenancy is added automatically.
    """
    class Meta:
        model = models.ContractType
        exclude = ['tenancy']


class BaseComponentForm(forms.ModelForm):
    """A form for the user to set the fields of a base component.
    Tenancy is added automatically.
    """
    class Meta:
        model = models.BaseComponent
        exclude = ['tenancy']


class VATRateForm(forms.ModelForm):
    """A form for the user to set the fields of a VAT rate.
    Tenancy is added automatically.
    """
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if end_date and end_date < start_date:
            raise forms.ValidationError(
                "End date should be on or after start date."
            )

        if start_date < datetime.date.today():
            raise forms.ValidationError(
                "Start date can only be today or in the future."
            )

        percentage = cleaned_data.get("percentage")
        if percentage > 100.0:
            raise forms.ValidationError(
                "Percentage should be in the range of 0.0% to 100.0%."
            )

    class Meta:
        model = models.VATRate
        exclude = ['tenancy', 'successor_vat_rate']


class ContractForm(forms.ModelForm):
    """A form for the user to set the fields of a contract.
    Tenancy is added automatically.
    The user can choose contract type from a drop-down menu.
    """
    def filter_selectors(self, tenancy):
        self.fields['contract_type'].queryset = \
            models.ContractType.objects.filter(tenancy=tenancy)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('invoicing_period') == self.instance.CUSTOM:
            if not cleaned_data.get('invoicing_amount_of_days'):
                raise forms.ValidationError(
                    "Fill in the amount of days to invoice."
                )
        else:
            if cleaned_data.get('invoicing_amount_of_days'):
                raise forms.ValidationError(
                    "Only fill in the amount of days to invoice if choosing "
                    "Custom invoicing period."
                )

    class Meta:
        model = models.Contract
        exclude = [
            'tenancy', 'date_next_prolongation',
            'balance', 'base_amount', 'vat_amount', 'total_amount',
            'date_prev_prolongation', 'end_date', 'start_date'
        ]


class ContractSearchForm(forms.Form):
    """The form the user can use to search contracts in the contracts
    list page.
    Takes one or more inputs, and filters the queryset based on this.
    """
    name = forms.CharField(max_length=50, required=False)
    address = forms.CharField(max_length=50, required=False)
    contract_type = forms.CharField(
        max_length=50,
        required=False, widget=forms.TextInput(attrs={'size': 10})
    )
    period = forms.CharField(
        max_length=15,
        required=False, widget=forms.TextInput(attrs={'size': 8})
    )
    start_date = forms.DateField(
        required=False, widget=forms.DateInput(attrs={'size': 8})
    )
    end_date = forms.DateField(
        required=False, widget=forms.DateInput(attrs={'size': 8})
    )
    next_invoice_date = forms.DateField(
        required=False, widget=forms.DateInput(attrs={'size': 8})
    )
    total_amount = forms.FloatField(
        required=False,
        widget=forms.TextInput(attrs={'size': 8, 'style': 'text-align: right'})
    )
    balance = forms.FloatField(
        required=False,
        widget=forms.TextInput(attrs={'size': 8, 'style': 'text-align: right'})
    )

    def filter_queryset(self, qs):
        if self.cleaned_data.get('contract_type'):
            qs = qs.filter(
                contract_type__description__icontains=self.cleaned_data.get(
                    'contract_type'
                )
            )
        if self.cleaned_data.get('period'):
            # Use only the first letter of the period
            qs = qs.filter(
                invoicing_period__istartswith=self.cleaned_data.get(
                    'period'
                )[0]
            )
        if self.cleaned_data.get('start_date'):
            qs = qs.filter(
                start_date=self.cleaned_data.get(
                    'start_date'
                )
            )
        if self.cleaned_data.get('end_date'):
            qs = qs.filter(
                end_date=self.cleaned_data.get(
                    'end_date'
                )
            )
        if self.cleaned_data.get('next_invoice_date'):
            qs = qs.filter(
                date_next_prolongation=self.cleaned_data.get(
                    'next_invoice_date'
                )
            )
        if self.cleaned_data.get('total_amount'):
            qs = qs.filter(
                total_amount=self.cleaned_data.get(
                    'total_amount'
                )
            )
        if self.cleaned_data.get('balance'):
            qs = qs.filter(
                balance=self.cleaned_data.get(
                    'balance'
                )
            )
        if self.cleaned_data.get('name'):
            qs = qs.filter(
                contractperson__name__icontains=self.cleaned_data.get(
                    'name'
                )
            )
        if self.cleaned_data.get('address'):
            # Filter both the address and the city
            qs = qs.filter(
                contractperson__address__icontains=self.cleaned_data.get(
                    'address'
                )
            ) | qs.filter(
                contractperson__city__icontains=self.cleaned_data.get(
                    'address'
                )
            )

        return qs


class ComponentForm(forms.ModelForm):
    """A form for the user to set the fields of a component."""
    def filter_selectors(self, tenancy):
        """Filter the querysets of the selectors for base component
        and VAT rate based on the tenancy and the VAT rate's end date.
        """
        self.fields['base_component'].queryset = \
            models.BaseComponent.objects.filter(
                tenancy=tenancy
            )
        self.fields['vat_rate'].queryset = \
            models.VATRate.objects.filter(
                tenancy=tenancy,
                end_date__isnull=True
            )

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
                    "Please specify unit amount and number of units for unit "
                    + unit_id.__str__()
                    + ". Do not specify base amount."
                )
            if not unit_amount or not number_of_units:
                raise forms.ValidationError(
                    "Please specify unit amount and number of units for unit "
                    + unit_id.__str__() + "."
                )
        else:
            if not base_amount:
                raise forms.ValidationError(
                    "Please specify a base amount for this component."
                )
            if unit_amount or number_of_units:
                raise forms.ValidationError(
                    "Please specify a base amount for this component. "
                    "Do not specify unit amount and number of units."
                )

        # Check that end date is after start date
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError(
                "Start date cannot be after end date."
            )

    class Meta:
        model = models.Component
        exclude = [
            'contract', 'vat_amount', 'total_amount', 'tenancy',
            'date_next_prolongation', 'unit_id', 'date_prev_prolongation',
            'end_date'
        ]


class ContractPersonFormSet(forms.BaseModelFormSet):
    """A form for the user to set the fields of a contract person."""
    def clean(self):
        super().clean()
        total_percentage = 0
        for form in self.forms:
            if self._should_delete_form(form):
                continue

            cleaned_data = form.clean()
            payment_method = cleaned_data.get("payment_method")
            iban = cleaned_data.get("iban")
            mandate = cleaned_data.get("mandate")

            if payment_method == models.ContractPerson.DIRECT_DEBIT:
                if not iban or not mandate:
                    raise forms.ValidationError(
                        "Please provide an iban and a mandate."
                    )

            start_date = cleaned_data.get("start_date")
            end_date = cleaned_data.get("end_date")
            if end_date and start_date and end_date < start_date:
                raise forms.ValidationError(
                    "End date should be after start date."
                )

            percentage = cleaned_data.get('percentage_of_total')
            if percentage:
                total_percentage += percentage

        if total_percentage > 100:
            raise forms.ValidationError(
                'Total of all persons exceeding 100% by '
                + (total_percentage - 100).__str__()
                + '%'
            )
        if total_percentage < 100:
            raise forms.ValidationError(
                'Total of all persons smaller than 100% by '
                + (100 - total_percentage).__str__()
                + '%'
            )


class DeactivationForm(forms.ModelForm):
    """Form with only one entry for the end date of a model.
    It validates that the end date is on or after the start date.
    """
    def clean(self):
        if self.instance.end_date:
            raise forms.ValidationError(
                "This VAT rate has already been deactivated"
            )

        cleaned_data = super().clean()
        end_date = cleaned_data.get("end_date")
        if end_date and end_date < self.instance.start_date:
            raise forms.ValidationError(
                "End date must be on or after "
                + self.instance.start_date.__str__()
            )

        return cleaned_data


class ComponentDeactivationForm(DeactivationForm):
    def clean(self):
        cleaned_data = super().clean()
        contract_end = self.instance.contract.end_date
        if contract_end and cleaned_data.get('end_data') > contract_end:
            raise forms.ValidationError(
                "End date cannot be past contract end date: "
                + self.instance.contract.end_date.__str__()
            )

    class Meta:
        model = models.Component
        fields = ['end_date']


class ContractDeactivationForm(DeactivationForm):
    class Meta:
        model = models.Contract
        fields = ['end_date']
