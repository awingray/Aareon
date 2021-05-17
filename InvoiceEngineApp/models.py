import datetime

from django.db import models, transaction
from django.db.models import Q, F


def get_next_invoice_id():
    """Static function to return the highest possible invoice id and invoice
    line id. Function needed because the ids are needed for other objects to
    refer to in their foreign key. This is done before the invoices and invoice
    lines are added to the database, so automatic primary keys have not been
    generated yet.
    """
    next_invoice_id = 0
    next_invoice_line_id = 0
    if Invoice.objects.exists():
        next_invoice_id = Invoice.objects.aggregate(
            models.Max('invoice_id')
        ).get('invoice_id__max') + 1
        next_invoice_line_id = InvoiceLine.objects.aggregate(
            models.Max('invoice_line_id')
        ).get('invoice_line_id__max') + 1

    return next_invoice_id, next_invoice_line_id


class Tenancy(models.Model):
    """This class represents a company. Only a user with the same username as
    the tenancy_id has access to this company and all its data. Therefore,
    every other object (indirectly) foreign-keys to this object.
    """
    company_id = models.AutoField(primary_key=True)
    tenancy_id = models.PositiveIntegerField()
    name = models.CharField(max_length=30)
    number_of_contracts = models.PositiveIntegerField(default=0)
    last_invoice_number = models.PositiveIntegerField(default=0)
    date_next_prolongation = models.DateField(null=True, blank=True)
    days_until_invoice_expiration = models.PositiveSmallIntegerField(
        default=14
    )

    def __str__(self):
        return self.name

    def create(self, kwargs):
        pass

    def get_details(self):
        """Method to print all fields and their values."""
        return {
            'name': self.name,
            'number of contracts': self.number_of_contracts,
            'last invoice number': self.last_invoice_number,
            'date of next prolonging': self.date_next_prolongation,
            'days until invoice expiration': self.days_until_invoice_expiration
        }

    def invoice_contracts(self):
        """"Method to go over all components linked to this tenancy, and
        to create invoices, invoice lines, collections, and general ledger
        posts for each of them.

        The ids for invoices and invoice lines have to be set manually,
        because they will be linked to by other objects. It is not possible
        to link after entry into the database.
        """
        date_today = datetime.date.today()

        # Load all components into memory
        components = list(
            self.component_set.filter(
                (Q(contract__status=Contract.ACTIVE)
                 | Q(contract__status=Contract.ENDED))
                & Q(date_next_prolongation__isnull=False)
                & Q(contract__date_next_prolongation__isnull=False)
                & Q(contract__date_next_prolongation__lte=date_today)
            ).order_by(
                'contract_id'
            ).select_related(
                'contract__contract_type', 'vat_rate', 'base_component'
            )
        )

        if not components:
            # There are no contracts to prolong
            return

        # Load all contract persons into memory
        contract_persons = list(
            self.contractperson_set.filter(
                contract__date_next_prolongation__isnull=False,
                contract__date_next_prolongation__lte=date_today
            ).order_by('contract_id')
        )

        # Create lists to store the generated objects
        # This is to use one single database transaction at the end
        new_invoices = []
        new_invoice_lines = []
        new_gl_posts = []
        new_collections = []

        # Set the id for the next invoice & invoice line.
        # Take the highest id that is currently in the database and add 1
        next_invoice_id, next_invoice_line_id = get_next_invoice_id()

        # Create an invoice for the first component's contract
        invoice = components[0].contract.invoice(
            date_today, next_invoice_id, self
        )
        new_invoices.append(invoice)
        next_invoice_id += 1
        previous_contract = components[0].contract_id

        # Loop over all components to create invoice lines for them
        for component in components:
            # Create a new invoice only when a new contract is reached
            # This is possible because components are ordered by contract_id
            if component.contract_id != previous_contract:
                # Invoice for contract x is finished
                # Generate collections for contract x
                while contract_persons and \
                        contract_persons[0].contract_id == invoice.contract_id:
                    contract_persons[0].invoice(self, invoice, new_collections)
                    contract_persons.pop(0)

                # Create GL posts for the finished invoice
                invoice.create_gl_post(new_gl_posts)

                # Create an invoice for the next contract
                invoice = component.contract.invoice(
                    date_today, next_invoice_id, self
                )
                new_invoices.append(invoice)
                next_invoice_id += 1

            # Create an invoice line and associated GL posts for this component
            component.invoice(
                next_invoice_line_id, invoice, new_invoice_lines, new_gl_posts
            )
            next_invoice_line_id += 1
            previous_contract = component.contract_id

        # Finish the final invoice
        while contract_persons and \
                contract_persons[0].contract_id == invoice.contract_id:
            contract_persons[0].invoice(self, invoice, new_collections)
            contract_persons.pop(0)

        invoice.create_gl_post(new_gl_posts)

        # End of main program loop
        # Save the changes made to the database in one transaction
        # If one fails, they will all fail
        with transaction.atomic():
            # Loop over the components and associated contracts to update them
            # Bulk update might overload the CPU in this case
            previous_contract = -1
            for component in components:
                if component.contract_id != previous_contract:
                    component.contract.save(
                        update_fields=[
                            'balance',
                            'date_next_prolongation',
                            'date_prev_prolongation',
                            'base_amount',
                            'vat_amount',
                            'total_amount'
                        ]
                    )

                component.save(
                    update_fields=[
                        'date_next_prolongation',
                        'date_prev_prolongation',
                        'vat_rate',
                        'vat_amount',
                        'total_amount'
                    ]
                )
                previous_contract = component.contract_id

            Invoice.objects.bulk_create(new_invoices)
            InvoiceLine.objects.bulk_create(new_invoice_lines)
            GeneralLedgerPost.objects.bulk_create(new_gl_posts)
            Collection.objects.bulk_create(new_collections)

            # Save the tenancy with the new last_invoice_number
            self.save(update_fields=['last_invoice_number'])


class TenancyDependentModel(models.Model):
    """This abstract class is inherited by models which directly refer to the
    tenancy model in their foreign key.
    """
    tenancy = models.ForeignKey(Tenancy, on_delete=models.CASCADE)

    def create(self, kwargs):
        """Method called when an instance of this class is created, to set
        the tenancy.
        """
        self.tenancy_id = kwargs.get('company_id')

    class Meta:
        abstract = True


class ContractType(TenancyDependentModel):
    """This class represents a certain type of contract, for instance for
    different kinds of rental cars for which they can make contracts.
    """
    contract_type_id = models.AutoField(primary_key=True)
    code = models.PositiveIntegerField()
    type = models.CharField(max_length=1)
    description = models.CharField(max_length=50)
    gl_debit = models.CharField(max_length=10)
    gl_credit = models.CharField(max_length=10)

    def __str__(self):
        return self.description

    def can_update_or_delete(self):
        """Method to determine whether the instance can be updated
        or deleted.
        """
        return not self.contract_set.filter(
            date_prev_prolongation__isnull=False
        ).exists()


class BaseComponent(TenancyDependentModel):
    """The base component represents a basic unit for a contract line.
    In the case of a housing provider, this could for instance be one line
    specifying the rent price, and one line specifying any service costs.

    A base component always corresponds to a tenancy.
    """
    base_component_id = models.AutoField(primary_key=True)
    code = models.PositiveIntegerField()
    description = models.CharField(max_length=50)
    gl_debit = models.CharField(max_length=10)
    gl_credit = models.CharField(max_length=10)
    gl_dimension = models.CharField(max_length=10)
    unit_id = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return self.description \
               + " - unit " \
               + self.unit_id.__str__() if self.unit_id else self.description

    def can_update_or_delete(self):
        return not self.component_set.filter(
            date_prev_prolongation__isnull=False
        ).exists()


class VATRate(TenancyDependentModel):
    """The VAT rate defines the value added tax charged for a contract line.
    In the Netherlands, there are three types of VAT: none (0%), low (9%),
    or high (21%).

    A VAT rate always corresponds to a tenancy.
    """
    vat_rate_id = models.AutoField(primary_key=True)
    successor_vat_rate = models.OneToOneField(
        'self', null=True, on_delete=models.SET_NULL
    )
    type = models.PositiveIntegerField()
    description = models.CharField(max_length=30)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    percentage = models.FloatField()
    gl_account = models.CharField(max_length=10)
    gl_dimension = models.CharField(max_length=10)

    def __str__(self):
        return "Type " \
               + self.type.__str__() \
               + ": " \
               + self.description \
               + " - " \
               + self.percentage.__str__() \
               + "%"

    def can_update_or_delete(self):
        return not self.component_set.filter(
            date_prev_prolongation__isnull=False
        ).exists()

    def update_components(self, do_remove):
        with transaction.atomic():
            for component in self.component_set.select_related('contract'):
                if do_remove:
                    component.vat_rate = None
                component.remove_from_contract()
                component.update()

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        # Try to find other VAT rate with the same type
        # There should only be one active
        old_vat_rate_qs = self.tenancy.vatrate_set.filter(
            Q(type=self.type)
            & (Q(end_date__isnull=True) | Q(end_date__gte=self.start_date))
            & Q(start_date__lt=self.start_date)
        )
        old_vat_rate = None
        do_delete = False
        if old_vat_rate_qs.exists():
            old_vat_rate = old_vat_rate_qs.first()

            if old_vat_rate.can_update_or_delete():
                do_delete = True
            else:
                old_vat_rate.successor_vat_rate = self
                old_vat_rate.end_date = (self.start_date - datetime.timedelta(days=1))

        with transaction.atomic():
            if old_vat_rate:
                if do_delete:
                    old_vat_rate.delete()
                else:
                    old_vat_rate.save(
                        update_fields=['successor_vat_rate', 'end_date']
                    )
            super().save(
                force_insert=force_insert,
                force_update=force_update,
                using=using,
                update_fields=update_fields
            )

    def delete(self, using=None, keep_parents=False):
        with transaction.atomic():
            self.update_components(do_remove=True)
            super().delete(using, keep_parents)


class Contract(TenancyDependentModel):
    """The contract is an agreement between two parties (e.g. a company and a
    person). In this case, the person(s) agree to pay some amount per some time
    period in exchange for a service or product.
    """
    # Define options for invoicing period
    MONTH = 'M'
    QUARTER = 'Q'
    HALF_YEAR = 'H'
    YEAR = 'Y'
    CUSTOM = 'V'
    INVOICING_PERIOD_CHOICES = [
        (MONTH, 'Month'),
        (QUARTER, 'Quarter'),
        (HALF_YEAR, 'Half year'),
        (YEAR, 'Year'),
        (CUSTOM, 'Custom')
    ]

    DRAFT = 'F'
    ACTIVE = 'A'
    TERMINATED = 'T'
    ENDED = 'E'
    HISTORIC = 'H'
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (ACTIVE, 'Active'),
        (TERMINATED, 'Terminated'),
        (ENDED, 'Ended'),
        (HISTORIC, 'Historic')
    ]

    # Model fields
    contract_id = models.AutoField(primary_key=True)
    external_customer_id = models.PositiveIntegerField()
    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default=DRAFT
    )

    contract_type = models.ForeignKey(ContractType, on_delete=models.CASCADE)
    invoicing_period = models.CharField(
        max_length=1,
        choices=INVOICING_PERIOD_CHOICES,
        default=MONTH
    )
    # Only not null if invoicing_period is custom
    invoicing_amount_of_days = models.PositiveSmallIntegerField(
        null=True, blank=True
    )

    # Dates
    start_date = models.DateField(null=True, default=None, blank=True)
    end_date = models.DateField(null=True, blank=True)
    date_prev_prolongation = models.DateField(null=True, default=None)
    date_next_prolongation = models.DateField(null=True, default=None)

    # General ledger
    gl_dimension_1 = models.CharField(max_length=10)
    gl_dimension_2 = models.CharField(max_length=10)

    # Accumulated fields
    balance = models.FloatField(default=0.0)
    base_amount = models.FloatField(default=0.0)
    vat_amount = models.FloatField(default=0.0)
    total_amount = models.FloatField(default=0.0)

    def __str__(self):
        return self.contract_type.description

    def get_components(self):
        return self.component_set.all()

    def has_components(self):
        return self.component_set.exists()

    def get_contract_persons(self):
        return self.contractperson_set.all()

    def has_contract_persons(self):
        return self.contractperson_set.exists()

    def get_invoices(self):
        return self.invoice_set.all()

    def get_period(self):
        for key, value in self.INVOICING_PERIOD_CHOICES:
            if key == self.invoicing_period:
                return value

    def create(self, kwargs):
        super().create(kwargs)
        self.tenancy.number_of_contracts = F('number_of_contracts') + 1
        self.tenancy.save(update_fields=['number_of_contracts'])

    def can_update_or_delete(self):
        return not self.is_active()

    def can_activate(self):
        """Return whether a contract can be activated for invoicing.
        This is only possible if it has contract persons, components,
        and a start date.
        """
        return (self.has_contract_persons()
                and self.start_date
                and self.has_components())

    def activate(self):
        """Activate a contract so that it can be invoiced."""
        self.date_next_prolongation = self.start_date
        self.status = Contract.ACTIVE
        with transaction.atomic():
            self.contractperson_set.filter(
                start_date__lt=self.start_date
            ).update(
                start_date=self.start_date
            )
            self.component_set.filter(
                start_date__lt=self.start_date
            ).update(
                start_date=self.start_date
            )
        self.save()

    def is_active(self):
        """Returns whether or not this contract is active for invoicing."""
        return self.status == Contract.ACTIVE

    def can_deactivate(self):
        return self.is_active() and not self.date_prev_prolongation

    def deactivate(self):
        self.status = Contract.DRAFT
        self.date_next_prolongation = None
        self.save()

    def terminate(self):
        components = self.component_set.filter(
            Q(end_date__isnull=True) | Q(end_date__gt=self.end_date)
        )
        components.update(end_date=self.end_date)

        if self.end_date == (self.date_next_prolongation
                             - datetime.timedelta(days=1)):
            # No need to invoice this contract in the future
            self.date_next_prolongation = None
        elif self.end_date < self.date_next_prolongation:
            # Issue a correction invoice
            invoice_id, invoice_line_id = get_next_invoice_id()
            invoice = self.create_invoice(
                datetime.date.today(),
                invoice_id,
                self.tenancy
            )

            new_invoice_lines = []
            new_gl_posts = []

            for component in components:
                component.create_correction_invoice_line(
                    invoice_line_id,
                    invoice,
                    new_invoice_lines,
                    new_gl_posts
                )
                invoice_line_id += 1

            with transaction.atomic():
                invoice.save()
                InvoiceLine.objects.bulk_create(new_invoice_lines)
                GeneralLedgerPost.objects.bulk_create(new_gl_posts)
                self.tenancy.save(update_fields=['last_invoice_number'])

    def delete(self, using=None, keep_parents=False):
        self.tenancy.number_of_contracts = F('number_of_contracts') - 1
        with transaction.atomic():
            self.tenancy.save(update_fields=['number_of_contracts'])
            super().delete(using, keep_parents)

    def compute_date_next_prolongation(self, previous_date):
        """Based on the invoicing period and the date of the last invoice,
        compute the date on which to invoice the contract next.
        """
        month = previous_date.month
        year = previous_date.year
        day = previous_date.day
        if self.invoicing_period == self.MONTH:
            month += 1
        elif self.invoicing_period == self.QUARTER:
            month += 3
        elif self.invoicing_period == self.HALF_YEAR:
            month += 6
        elif self.invoicing_period == self.YEAR:
            year += 1
        elif self.invoicing_period == self.CUSTOM:
            return previous_date + datetime.timedelta(
                days=self.invoicing_amount_of_days
            )

        # Shift year by one if the 12th month is passed
        if month > 12:
            month %= 12
            year += 1

        if month == 2 and day > 28:
            # Correct for February & keep leap years into account
            # Note that there is no check for year % 100 == 0,
            # which is not a leap year unless year % 400 == 0
            day = 29 if year % 4 == 0 else 28
        elif day == 31 and month in [4, 6, 9, 11]:
            # Correct for months that have 30 days
            day = 30

        return datetime.date(year, month, day)

    def invoice(self, date_today, next_id, tenancy):
        self.date_prev_prolongation = self.date_next_prolongation

        if self.end_date and self.end_date < self.date_next_prolongation:
            # Only partially invoice the period (logic in component)
            self.date_next_prolongation = None
        else:
            self.date_next_prolongation = self.compute_date_next_prolongation(
                self.date_next_prolongation
            )

        return self.create_invoice(date_today, next_id, tenancy)

    def create_invoice(self, date_today, next_id, tenancy):
        tenancy.last_invoice_number += 1
        # Do not specify amounts (added from the invoice lines)
        return Invoice(
            invoice_id=next_id,
            tenancy=tenancy,
            contract=self,
            external_customer_id=self.external_customer_id,
            description="Invoice: " + date_today.__str__(),
            date=date_today,
            expiration_date=date_today + datetime.timedelta(
                days=tenancy.days_until_invoice_expiration
            ),
            invoice_number=tenancy.last_invoice_number,
            gl_account=self.contract_type.gl_debit,
        )


class Component(TenancyDependentModel):
    """A Contract is built up of one or more components.
    These 'contract lines' specify the amounts and services.
    """
    component_id = models.AutoField(primary_key=True)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    base_component = models.ForeignKey(BaseComponent, on_delete=models.CASCADE)
    vat_rate = models.ForeignKey(
        VATRate, null=True, blank=True, on_delete=models.SET_NULL
    )
    description = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    date_prev_prolongation = models.DateField(
        null=True, blank=True, default=None
    )
    date_next_prolongation = models.DateField()
    base_amount = models.FloatField(null=True, blank=True)
    vat_amount = models.FloatField(default=0.0)
    total_amount = models.FloatField(default=0.0)
    unit_id = models.CharField(max_length=10, null=True, blank=True)
    unit_amount = models.FloatField(null=True, blank=True)
    number_of_units = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.description

    def create(self, kwargs):
        """Also check if this component replaces an existing component.
        """
        super().create(kwargs)
        self.contract = Contract.objects.get(
            contract_id=kwargs.get('contract_id')
        )

        self.date_next_prolongation = self.start_date
        self.unit_id = self.base_component.unit_id
        self.end_date = self.contract.end_date  # May still be None

        self.set_derived_fields()

        # Check if this component replaces an existing active one
        old_component_qs = self.contract.component_set.filter(
            Q(base_component=self.base_component)
            & (Q(end_date__isnull=True) | Q(end_date__gte=self.start_date))
        )
        is_corrected = False
        invoice = None
        invoice_line_id = 0
        new_invoice_lines = []
        new_gl_posts = []
        for old_component in old_component_qs:
            if not old_component.date_prev_prolongation:
                # If the old component has not been invoiced, simply delete it
                old_component.delete()
            else:
                # The old component has been invoiced, so simply end it and
                # issue a correction invoice if necessary
                old_component.remove_from_contract()
                needs_correction = False

                # Set the end date of the old component if necessary
                if not old_component.end_date \
                        or (old_component.end_date
                            and self.start_date <= old_component.end_date):
                    if old_component.date_next_prolongation:
                        needs_correction = self.start_date \
                                        < old_component.date_next_prolongation
                    else:
                        needs_correction = self.start_date \
                                        <= old_component.end_date

                    old_component.end_date = (self.start_date
                                              - datetime.timedelta(days=1))

                # Check if the component has retroactively been completely
                # replaced from the start by the new one
                if old_component.end_date < old_component.start_date:
                    old_component.end_date = old_component.start_date

                if needs_correction:
                    if not is_corrected:
                        invoice_id, invoice_line_id = get_next_invoice_id()

                        invoice = self.contract.create_invoice(
                            datetime.date.today(),
                            invoice_id,
                            self.tenancy
                        )
                        is_corrected = True

                    # Create two invoice lines, correction & new amount
                    self.process_retroactive_price_change(
                        old_component,
                        invoice,
                        invoice_line_id,
                        new_invoice_lines,
                        new_gl_posts
                    )
                    invoice_line_id += 2

        if self.contract.date_prev_prolongation and not is_corrected:
            # The contract has been invoiced before, so check if this new
            # component needs to be invoiced for the period from its start
            # date until the next invoicing date of the contract
            if self.contract.date_next_prolongation \
                and self.start_date < self.contract.date_next_prolongation \
                    or not self.contract.date_next_prolongation:
                # Case 1: The period up to (and not including) the
                # date_next_prolongation has been invoiced, so there needs
                # to be an invoice for this new component from its start
                # date up the contract's date_next_prolongation

                # Case 2: The contract has ended, but this component was added
                # with a start_date before contract.end_date, so need to
                # invoice this component for the period between its start_date
                # and end_date

                invoice_id, invoice_line_id = get_next_invoice_id()
                invoice = self.contract.create_invoice(
                    datetime.date.today(),
                    invoice_id,
                    self.tenancy
                )
                self.invoice(
                    invoice_line_id,
                    invoice,
                    new_invoice_lines,
                    new_gl_posts
                )

        # If the contract was invoiced, save all associated objects to the
        # database in one transaction. Otherwise just save the contract.
        if invoice:
            new_collections = []
            for person in self.contract.contractperson_set:
                person.invoice(self.tenancy, invoice, new_collections)

            invoice.create_gl_post(new_gl_posts)

            with transaction.atomic():
                invoice.save()
                InvoiceLine.objects.bulk_create(new_invoice_lines)
                GeneralLedgerPost.objects.bulk_create(new_gl_posts)
                Collection.objects.bulk_create(new_collections)
                self.tenancy.save(update_fields=['last_invoice_number'])
                self.contract.save()
        else:
            self.contract.save()

    def process_retroactive_price_change(self, old_component,
                                         correction_invoice,
                                         next_invoice_line_id,
                                         new_invoice_lines,
                                         new_gl_posts):
        """Create a correction invoice consisting of two invoice lines:
        1. correction: remove the amount that was overpaid for the old
        component (negative).
        2. new: add the amount that needs to be paid for the new
        component (positive).

        The amount on the resulting invoice can be positive (price raise) or
        negative (price drop).
        """
        base_factor, vat_factor, total_factor, unit_factor = \
            old_component.create_correction_invoice_line(
                next_invoice_line_id,
                correction_invoice,
                new_invoice_lines,
                new_gl_posts
            )

        next_invoice_line_id += 1

        self.create_invoice_line(
            next_invoice_line_id,
            correction_invoice,
            self.base_amount*base_factor,
            self.vat_amount*vat_factor,
            self.total_amount*total_factor,
            self.unit_amount*unit_factor,
            new_invoice_lines,
            new_gl_posts
        )

        self.date_prev_prolongation = old_component.date_prev_prolongation
        old_component.date_next_prolongation = None

        old_component.save()

    def create_correction_invoice_line(self, next_invoice_line_id, invoice,
                                       new_invoice_lines, new_gl_posts):
        invoice_lines = self.invoiceline_set.filter(
            invoice__date__lte=self.date_prev_prolongation
        ).select_related('invoice').order_by('-invoice__date')

        base_amount = 0.0
        vat_amount = 0.0
        unit_amount = 0.0
        total_amount = 0.0

        for invoice_line in invoice_lines:
            base_amount += invoice_line.base_amount
            vat_amount += invoice_line.vat_amount
            unit_amount += invoice_line.unit_amount
            total_amount += invoice_line.total_amount

            if invoice_line.invoice.date \
                    <= self.end_date + datetime.timedelta(days=1):
                break

        self.create_invoice_line(
            next_invoice_line_id,
            invoice,
            -base_amount,
            -vat_amount,
            -total_amount,
            -unit_amount,
            new_invoice_lines,
            new_gl_posts
        )

        base_factor = base_amount/self.base_amount if self.base_amount else 0
        vat_factor = vat_amount/self.vat_amount if self.vat_amount else 0
        total_factor = total_amount/self.total_amount  # Cannot be 0
        unit_factor = unit_amount/self.unit_amount if self.unit_amount else 0

        return base_factor, vat_factor, total_factor, unit_factor

    def update(self):
        if self.vat_amount and not self.vat_rate:
            self.total_amount -= self.vat_amount
            self.vat_amount = 0
        self.set_derived_fields()

        with transaction.atomic():
            self.contract.save()
            self.save()

    def can_update_or_delete(self):
        return self.date_prev_prolongation is None

    def remove_from_contract(self):
        self.contract.total_amount -= self.total_amount
        self.contract.vat_amount -= self.vat_amount
        # Subtract VAT from total to prevent checking for units
        self.contract.base_amount -= (self.total_amount - self.vat_amount)

    def delete(self, using=None, keep_parents=False):
        # Remove the amounts from the contract
        self.remove_from_contract()

        with transaction.atomic():
            self.contract.save(
                update_fields=['total_amount', 'vat_amount', 'base_amount']
            )
            super().delete(using, keep_parents)

    def deactivate(self):
        # Deactivation is setting the end date. If this is set to a date which
        # has already been invoiced, send a correction invoice
        # Otherwise it will be handled in the invoicing cycle
        if self.end_date < self.date_next_prolongation:
            invoice_id, invoice_line_id = get_next_invoice_id()

            invoice = self.contract.create_invoice(
                datetime.date.today,
                invoice_id,
                self.tenancy
            )

            new_invoice_lines = []
            new_gl_posts = []

            self.create_correction_invoice_line(
                invoice_line_id,
                invoice,
                new_invoice_lines,
                new_gl_posts
            )

            self.remove_from_contract()

            new_collections = []
            for person in self.contract.contractperson_set:
                person.invoice(self.tenancy, invoice, new_collections)

            invoice.create_gl_post(new_gl_posts)

            with transaction.atomic():
                self.contract.save()
                new_invoice_lines[0].save()
                GeneralLedgerPost.objects.bulk_create(new_gl_posts)
                Collection.objects.bulk_create(new_collections)
                invoice.save()
                self.tenancy.save(update_fields=['last_invoice_number'])

    def set_derived_fields(self):
        """Compute and set the amounts on the component and the associated
        contract.
        """
        amount = self.base_amount
        if not amount:
            amount = self.number_of_units * self.unit_amount

        if self.vat_rate:
            self.vat_amount = amount * self.vat_rate.percentage/100

        self.total_amount = amount + self.vat_amount

        # Update contract
        self.contract.total_amount += self.total_amount
        self.contract.vat_amount += self.vat_amount
        self.contract.base_amount += amount

    def create_invoice_line(self, next_id, invoice, base_amount, vat_amount,
                            total_amount, unit_amount,
                            new_invoice_lines, new_gl_posts):
        invoice_line = InvoiceLine(
            invoice_line_id=next_id,
            component=self,
            invoice=invoice,
            description=self.description,
            base_amount=base_amount,
            vat_amount=vat_amount,
            total_amount=total_amount,
            vat_type=self.vat_rate.type if self.vat_rate else None,

            gl_account=self.base_component.gl_credit,
            gl_dimension_base_component=self.base_component.gl_dimension,
            gl_dimension_contract_1=self.contract.gl_dimension_1,
            gl_dimension_contract_2=self.contract.gl_dimension_2,
            gl_dimension_vat=self.vat_rate.gl_dimension if self.vat_rate else None,

            number_of_units=self.number_of_units,
            unit_price=unit_amount,
            unit_id=self.unit_id
        )

        # To prevent doing maths with units
        invoice.base_amount += total_amount - vat_amount
        invoice.vat_amount += vat_amount
        invoice.total_amount += total_amount
        invoice.balance += total_amount
        self.contract.balance += total_amount

        # Create gl posts (one if no VAT, otherwise two)
        invoice_line.create_gl_posts(new_gl_posts)
        new_invoice_lines.append(invoice_line)

    def invoice(self, next_id, invoice, new_invoice_lines, new_gl_posts):
        if self.contract.date_next_prolongation \
                and self.start_date >= self.contract.date_next_prolongation:
            return

        base_amount = self.base_amount
        unit_amount = self.unit_amount
        total_amount = self.total_amount
        vat_amount = self.vat_amount

        start_date_period = self.contract.date_prev_prolongation  # 'today'
        end_date_period = self.contract.date_next_prolongation
        if not end_date_period:
            end_date_period = self.contract.compute_date_next_prolongation(
                start_date_period
            )

        # Check if the VAT is different for this period
        if self.vat_rate.end_date \
                and self.vat_rate.end_date < start_date_period:
            if self.vat_rate.successor_vat_rate:
                if self.vat_rate.percentage != self.vat_rate.successor_vat_rate.percentage:
                    self.vat_rate = self.vat_rate.successor_vat_rate

                    total_without_vat = total_amount - vat_amount
                    vat_amount = (total_without_vat
                                  * self.vat_rate.percentage / 100)
                    total_amount = total_without_vat + vat_amount

                    self.contract.vat_amount -= self.vat_amount
                    self.contract.total_amount -= self.vat_amount

                    self.vat_amount = vat_amount
                    self.total_amount = total_amount

                    self.contract.vat_amount += self.vat_amount
                    self.contract.total_amount += self.vat_amount
            else:
                self.vat_rate = None

        component_ending = (self.contract.date_next_prolongation
                            and self.end_date
                            and self.end_date < end_date_period)
        contract_ending = not self.contract.date_next_prolongation
        component_starting = (start_date_period
                              < self.date_next_prolongation
                              <= end_date_period)

        end_date_to_invoice = (self.end_date
                               if component_ending or contract_ending
                               else self.contract.date_next_prolongation)

        if component_ending or contract_ending or component_starting:
            # Case 1: end date of component is within next invoicing period
            # Case 2: end date of contract is within next invoicing period
            # Case 3: this component started some time during invoicing period
            # Either way, invoice the period between start_date_period and
            # the end date of the component
            days_invoicing_period = (end_date_period - start_date_period).days
            days_to_invoice = (end_date_to_invoice - self.date_next_prolongation).days + 1

            base_amount = base_amount / days_invoicing_period*days_to_invoice
            unit_amount = unit_amount / days_invoicing_period*days_to_invoice
            vat_amount = vat_amount / days_invoicing_period*days_to_invoice
            total_amount = total_amount / days_invoicing_period*days_to_invoice

            if component_ending:
                self.remove_from_contract()

            self.date_next_prolongation = (
                None if component_ending or contract_ending
                else self.contract.date_next_prolongation)

        else:
            self.date_next_prolongation = self.contract.date_next_prolongation

        self.date_prev_prolongation = self.contract.date_prev_prolongation

        self.create_invoice_line(
            next_id, invoice, base_amount, vat_amount,
            total_amount, unit_amount,
            new_invoice_lines, new_gl_posts
        )


class ContractPerson(TenancyDependentModel):
    """A contract contains one or more contract persons."""
    DIRECT_DEBIT = 'D'
    EMAIL = 'E'
    SMS = 'S'
    LETTER = 'L'
    INVOICE = 'I'

    PAYMENT_METHOD_CHOICES = [
        (DIRECT_DEBIT, 'direct debit'),
        (EMAIL, 'email'),
        (SMS, 'sms'),
        (LETTER, 'letter'),
        (INVOICE, 'invoice')
    ]

    contract_person_id = models.AutoField(primary_key=True)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    type = models.CharField(max_length=1, null=True, default=None)
    start_date = models.DateField(null=True, default=None)
    end_date = models.DateField(null=True, blank=True, default=None)
    name = models.CharField(max_length=50, null=True, default=None)
    address = models.CharField(max_length=50, null=True, default=None)
    city = models.CharField(max_length=50, null=True, default=None)
    payment_method = models.CharField(
        max_length=1,
        choices=PAYMENT_METHOD_CHOICES,
        default=INVOICE
    )
    iban = models.CharField(max_length=17, null=True, blank=True, default=None)
    mandate = models.PositiveIntegerField(null=True, blank=True, default=None)
    email = models.EmailField(null=True, default=None)
    phone = models.CharField(max_length=15, null=True, default=None)
    percentage_of_total = models.PositiveIntegerField(default=0.0)
    payment_day = models.PositiveIntegerField(null=True, default=None)

    def __str__(self):
        return "contract person " + self.name

    def can_delete(self):
        return not self.contract.start_date

    def invoice(self, tenancy, invoice, new_collections):
        """Create collection objects when the invoice has been finished."""
        new_collections.append(
            Collection(
                tenancy=tenancy,
                contract_person=self,
                invoice=invoice,
                payment_method=self.payment_method,
                payment_day=self.payment_day,
                mandate=self.mandate,
                iban=self.iban,
                amount=(self.percentage_of_total / 100) * invoice.total_amount
            )
        )


class Invoice(TenancyDependentModel):
    invoice_id = models.PositiveIntegerField(primary_key=True)
    # Ask if this should cascade
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    external_customer_id = models.PositiveIntegerField()
    description = models.CharField(max_length=50)
    base_amount = models.FloatField(default=0.0)
    vat_amount = models.FloatField(default=0.0)
    total_amount = models.FloatField(default=0.0)
    balance = models.FloatField(default=0.0)
    date = models.DateField()
    expiration_date = models.DateField()
    invoice_number = models.PositiveIntegerField()
    gl_account = models.CharField(max_length=10)

    def get_invoice_lines(self):
        return self.invoiceline_set.all()

    def create_gl_post(self, new_gl_posts):
        new_gl_posts.append(
            GeneralLedgerPost(
                tenancy=self.tenancy,
                invoice=self,
                invoice_line=None,
                date=self.date,
                gl_account=self.gl_account,
                gl_dimension_base_component=None,
                gl_dimension_contract_1=self.contract.gl_dimension_1,
                gl_dimension_contract_2=self.contract.gl_dimension_2,
                gl_dimension_vat=None,
                description="Debtors",
                amount_debit=self.total_amount,
                amount_credit=0.0
            )
        )


class InvoiceLine(models.Model):
    invoice_line_id = models.PositiveIntegerField(primary_key=True)
    component = models.ForeignKey(Component, on_delete=models.CASCADE)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    description = models.CharField(max_length=50)
    vat_type = models.PositiveIntegerField(null=True)
    base_amount = models.FloatField(null=True)
    vat_amount = models.FloatField(default=0.0)
    total_amount = models.FloatField(default=0.0)
    gl_account = models.CharField(max_length=10)
    gl_dimension_base_component = models.CharField(max_length=10)
    gl_dimension_contract_1 = models.CharField(max_length=10)
    gl_dimension_contract_2 = models.CharField(max_length=10)
    gl_dimension_vat = models.CharField(max_length=10, null=True)
    unit_price = models.FloatField(null=True)
    unit_id = models.CharField(max_length=10, null=True)
    number_of_units = models.FloatField(null=True)

    def create_gl_posts(self, new_gl_posts):
        total_without_vat = self.total_amount - self.vat_amount
        if total_without_vat:
            new_gl_posts.append(
                GeneralLedgerPost(
                    tenancy=self.invoice.tenancy,
                    invoice=None,  # This could be changed to invoice in needed
                    invoice_line=self,
                    date=self.invoice.date,
                    gl_account=self.gl_account,
                    gl_dimension_base_component=self.gl_dimension_base_component,
                    gl_dimension_contract_1=self.gl_dimension_contract_1,
                    gl_dimension_contract_2=self.gl_dimension_contract_2,
                    gl_dimension_vat=None,
                    description="Proceeds",
                    amount_credit=total_without_vat,
                    amount_debit=0.0
                )
            )

        # Only create a post for the general ledger for the VAT if applicable
        if self.vat_type:
            new_gl_posts.append(
                GeneralLedgerPost(
                    tenancy=self.invoice.tenancy,
                    invoice=None,
                    invoice_line=self,
                    date=self.invoice.date,
                    gl_account=self.component.vat_rate.gl_account,
                    gl_dimension_base_component=self.gl_dimension_base_component,
                    gl_dimension_contract_1=self.gl_dimension_contract_1,
                    gl_dimension_contract_2=self.gl_dimension_contract_2,
                    gl_dimension_vat=self.gl_dimension_vat,
                    description="VAT",
                    amount_credit=self.vat_amount,
                    amount_debit=0.0
                )
            )


class Collection(TenancyDependentModel):
    contract_person = models.ForeignKey(
        ContractPerson, on_delete=models.CASCADE
    )
    # Ask if this should cascade
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=1)
    payment_day = models.PositiveIntegerField()
    mandate = models.PositiveIntegerField(null=True)
    iban = models.CharField(max_length=17, null=True)
    amount = models.FloatField(default=0.0)

    def get_values_external_file(self):
        return [
            self.contract_person.name,
            self.contract_person.address,
            self.contract_person.city,
            self.payment_method,
            self.payment_day,
            self.invoice.invoice_number,
            self.invoice.date,
            self.contract_person.contract_id,
            self.invoice_id,
            self.amount,
            self.mandate,
            self.iban,
            self.contract_person.email,
            self.contract_person.phone
        ]


class GeneralLedgerPost(TenancyDependentModel):
    invoice = models.ForeignKey(Invoice, null=True, on_delete=models.CASCADE)
    invoice_line = models.ForeignKey(
        InvoiceLine, null=True, on_delete=models.CASCADE
    )
    date = models.DateField()
    gl_account = models.CharField(max_length=10)
    gl_dimension_base_component = models.CharField(null=True, max_length=10)
    gl_dimension_contract_1 = models.CharField(max_length=10)
    gl_dimension_contract_2 = models.CharField(max_length=10)
    gl_dimension_vat = models.CharField(null=True, max_length=10)
    description = models.CharField(max_length=30)
    amount_debit = models.FloatField()
    amount_credit = models.FloatField()
