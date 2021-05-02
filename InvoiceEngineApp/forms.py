from django import forms
from django.db import transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404
import datetime

from InvoiceEngineApp import models
from InvoiceEngineApp.models import Invoice, InvoiceLine, GeneralLedgerPost


class TenancyAdministratorForm(forms.ModelForm):
    """A form for the administrator to create a new tenancy.
    number_of_contracts and last_invoice_number are derived and should not be changed by users.
    """
    class Meta:
        model = models.Tenancy
        exclude = ['number_of_contracts', 'last_invoice_number',
                   'days_until_invoice_expiration', 'date_next_prolongation']


class TenancySubscriberForm(forms.ModelForm):
    """A form for the user to update a tenancy."""
    class Meta:
        model = models.Tenancy
        exclude = ['tenancy_id', 'name', 'number_of_contracts', 'last_invoice_number']


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

        percentage = cleaned_data.get("percentage")
        if percentage > 100.0:
            raise forms.ValidationError("Percentage should be in the range of 0.0% to 100.0%")

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
        self.instance.date_next_prolongation = self.instance.start_date
        self.instance.date_prolonged_until = None

        self.instance.tenancy.number_of_contracts += 1
        self.instance.tenancy.save()

    class Meta:
        model = models.Contract
        exclude = ['tenancy', 'invoicing_amount_type', 'date_next_prolongation',
                   'balance', 'base_amount', 'vat_amount', 'total_amount',
                   'date_prolonged_until'
                   ]


class ContractSearchForm(forms.Form):
    name = forms.CharField(max_length=50, required=False)
    address = forms.CharField(max_length=50, required=False)
    contract_type = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'size': 10}))
    period = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'size': 8}))
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'size': 8}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'size': 8}))
    next_invoice_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'size': 8}))
    total_amount = forms.FloatField(required=False, widget=forms.NumberInput(attrs={'size': 8}))
    balance = forms.FloatField(required=False, widget=forms.NumberInput(attrs={'size': 8}))

    def filter_queryset(self, qs):
        if self.cleaned_data.get('contract_type'):
            qs = qs.filter(contract_type__description__icontains=self.cleaned_data.get('contract_type'))
        if self.cleaned_data.get('period'):
            qs = qs.filter(invoicing_period__istartswith=self.cleaned_data.get('period')[0])
        if self.cleaned_data.get('start_date'):
            qs = qs.filter(start_date=self.cleaned_data.get('start_date'))
        if self.cleaned_data.get('end_date'):
            qs = qs.filter(end_date=self.cleaned_data.get('end_date'))
        if self.cleaned_data.get('next_invoice_date'):
            qs = qs.filter(next_date_prolong=self.cleaned_data.get('next_invoice_date'))
        if self.cleaned_data.get('total_amount'):
            qs = qs.filter(total_amount=self.cleaned_data.get('total_amount'))
        if self.cleaned_data.get('balance'):
            qs = qs.filter(balance=self.cleaned_data.get('balance'))
        if self.cleaned_data.get('name'):
            qs = qs.filter(contractperson__name__icontains=self.cleaned_data.get('name'))
        if self.cleaned_data.get('address'):
            qs = qs.filter(contractperson__address__icontains=self.cleaned_data.get('address')) \
                 | qs.filter(contractperson__city__icontains=self.cleaned_data.get('address'))

        return qs


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
        if end_date and end_date <= start_date:
            raise forms.ValidationError("End date should be after or on start date.")

    def finalize_creation(self, view_object):
        self.instance.tenancy = view_object.tenancy
        contract = get_object_or_404(
            models.Contract.objects.select_related('contract_type'),
            contract_id=view_object.kwargs.get('contract_id')
        )
        self.instance.contract = contract
        self.instance.date_next_prolongation = self.instance.start_date
        self.instance.date_prolonged_until = None
        self.instance.unit_id = self.instance.base_component.unit_id

        self.set_derived_fields()

        # When a new component is created,
        # try to find another active component that uses the same base component and end that one
        # This represents a price change for the old component, but the old component needs to remain (for audit trail)
        old_component_qs = self.instance.contract.component_set.filter(
            base_component=self.instance.base_component,
            end_date=None
        ).select_related('contract', 'vat_rate', 'base_component')
        if old_component_qs.exists():
            old_component = get_object_or_404(old_component_qs)
            old_component.end_date = self.instance.start_date - datetime.timedelta(days=1)  # End old component
            if old_component.end_date < old_component.start_date:
                # The old component was effectively cancelled
                old_component.end_date = old_component.start_date

            if old_component.end_date < old_component.date_prolonged_until:
                # If an invoice has gone out already, issue a correction
                self.process_retroactive_price_change(old_component)

        # A save for the contract is needed in any case, because the derived fields have to be saved as well
        self.instance.contract.save()

    def process_retroactive_price_change(self, old_component):
        """Create a correction invoice consisting of two invoice lines:
        1. correction: remove the amount that was overpaid for the old component (negative)
        2. new amount: add the amount that needs to be paid for the new component (positive)
        The amount on the resulting invoice can be positive (price raise) or negative (price drop)

        The correction period in this method is a multiple of the invoicing_period corresponding to the contract
        """

        # Following qs is non-empty, because the component has been invoiced after its end date
        invoice_lines_qs = old_component.invoiceline_set.filter(
            invoice__date__lt=old_component.date_prolonged_until
        ).order_by('-date')

        number_of_periods = 0
        # Loop over invoices until the one directly preceding the component's end date is found
        # This is necessary because multiple invoices may have gone out before addressing the price change
        start_date_correction_period = old_component.start_date  # For safety
        for invoice_line in invoice_lines_qs:
            number_of_periods += 1

            if invoice_line.date < old_component.end_date:
                start_date_correction_period = invoice_line.date
                break

        # The amount of days to correct for is determined by the date of the invoice that was issued before the end date
        # of the component: last_invoice_date - invoice_directly_before_component_end_date
        days_correction_period = (old_component.date_prolonged_until - start_date_correction_period).days
        days_wrongly_invoiced = (old_component.date_prolonged_until - old_component.end_date).days

        next_invoice_id = 0
        next_invoice_line_id = 0

        if Invoice.objects.exists():
            next_invoice_id = Invoice.objects.aggregate(
                Max('invoice_id')
            ).get('invoice_id__max') + 1
            next_invoice_line_id = InvoiceLine.objects.aggregate(
                Max('invoice_line_id')
            ).get('invoice_line_id__max') + 1

        # Create invoice. No need to increment counter as we are only creating one invoice
        correction_invoice = self.instance.contract.create_invoice(datetime.date.today(), next_invoice_id, self.instance.tenancy)

        # Create correction invoice lines & general ledger posts
        new_invoice_lines = []
        new_gl_posts = []
        old_component.create_invoice_lines(
            next_invoice_line_id,
            correction_invoice,
            -old_component.base_amount * number_of_periods / days_correction_period * days_wrongly_invoiced,
            -old_component.vat_amount * number_of_periods / days_correction_period * days_wrongly_invoiced,
            -old_component.total_amount * number_of_periods / days_correction_period * days_wrongly_invoiced,
            -old_component.unit_amount * number_of_periods / days_correction_period * days_wrongly_invoiced,
            new_invoice_lines,
            new_gl_posts
        )
        next_invoice_line_id += 1

        # Create invoice line for the new component
        self.instance.create_invoice_line(
            next_invoice_line_id,
            correction_invoice,
            self.instance.base_amount * number_of_periods / days_correction_period * days_wrongly_invoiced,
            self.instance.vat_amount * number_of_periods / days_correction_period * days_wrongly_invoiced,
            self.instance.total_amount * number_of_periods / days_correction_period * days_wrongly_invoiced,
            self.instance.unit_amount * number_of_periods / days_correction_period * days_wrongly_invoiced,
            new_invoice_lines,
            new_gl_posts
        )

        # Finish up the new component
        self.instance.date_prolonged_until = old_component.date_prolonged_until

        # Finish up the old component
        old_component.date_prolonged_until = old_component.end_date
        old_component.date_next_prolongation = None

        # Update the database (the contract is updated later)
        # The new component is saved automatically after this
        with transaction.atomic():
            correction_invoice.save()
            InvoiceLine.objects.bulk_create(new_invoice_lines)
            GeneralLedgerPost.objects.bulk_create(new_gl_posts)
            old_component.save()

        # Finish up the contract (saved in calling function)
        # Contract balance is updated when invoice lines are created
        self.instance.contract.base_amount -= old_component.base_amount
        self.instance.contract.vat_amount -= old_component.vat_amount
        self.instance.contract.total_amount -= old_component.total_amount

    def finalize_update(self):
        """Update the amounts on the component and on the corresponding contract."""
        self.set_derived_fields()
        self.instance.contract.save()

    def set_derived_fields(self):
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

    class Meta:
        model = models.Component
        exclude = ['contract', 'vat_amount', 'total_amount', 'tenancy',
                   'date_next_prolongation', 'unit_id', 'date_prolonged_until']


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
