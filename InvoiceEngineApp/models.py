import datetime
from django.db import models
from django.db.models import CheckConstraint, Q, F
from django.shortcuts import get_object_or_404


class Tenancy(models.Model):
    """The tenancy defines the organization using the model.  All other classes will have an (indirect) reference to the
    tenancy, in order to keep track of who is allowed to access the data.

    A tenant can manage multiple companies, but one company cannot be managed by multiple tenants. Therefore, the
    company_id is the primary key.
    """
    company_id = models.AutoField(primary_key=True)
    tenancy_id = models.PositiveIntegerField()
    name = models.CharField(max_length=30)
    number_of_contracts = models.PositiveIntegerField(default=0)
    last_invoice_number = models.PositiveIntegerField(default=0)
    day_next_prolong = models.DateField()
    days_until_invoice_expiration = models.PositiveSmallIntegerField(default=14)

    def __str__(self):
        return self.name

    def get_details(self):
        """Method to print all fields and their values."""
        return {'name': self.name,
                'number of contracts': self.number_of_contracts,
                'last invoice number': self.last_invoice_number,
                'date of next prolonging': self.day_next_prolong,
                'days until invoice expiration': self.days_until_invoice_expiration
                }

    def invoice_contracts(self):
        # Get the highest invoice id from the database
        next_invoice_id = 0
        next_invoice_line_id = 0

        if Invoice.objects.exists():
            next_invoice_id = Invoice.objects.aggregate(models.Max('invoice_id')).get('invoice_id__max') + 1
            next_invoice_line_id = \
                InvoiceLine.objects.aggregate(models.Max('invoice_line_id')).get('invoice_line_id__max') + 1

        # Load all information about contracts into memory to reduce database querying
        contracts = self.contract_set.select_related('contract_type')

        # Loop over all contracts and call their create_invoice() method
        new_invoices = []
        new_invoice_lines = []
        for contract in contracts:
            invoice, invoice_lines, next_invoice_line_id = contract.create_invoice(
                self.days_until_invoice_expiration,
                next_invoice_id,
                next_invoice_line_id
            )

            next_invoice_id += 1

            new_invoices.append(invoice)
            new_invoice_lines.extend(invoice_lines)

        print("Received all new objects")
        print("Starting bulk create at " + datetime.datetime.now().__str__())
        Invoice.objects.bulk_create(new_invoices)
        InvoiceLine.objects.bulk_create(new_invoice_lines)


class TenancyDependentModel(models.Model):
    tenancy = models.ForeignKey(Tenancy, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class ContractType(TenancyDependentModel):
    """A company may have contracts for different services, for instance a housing provider which has different
    contracts for different types of apartments, parking spaces, garages, etc.

    A contract type always corresponds to a tenancy.
    """
    contract_type_id = models.AutoField(primary_key=True)
    code = models.PositiveIntegerField()
    type = models.CharField(max_length=1)
    description = models.CharField(max_length=50)
    general_ledger_debit = models.CharField(max_length=10)
    general_ledger_credit = models.CharField(max_length=10)

    def __str__(self):
        return self.description

    def get_details(self):
        """Method to print all fields and their values."""
        return {'tenancy': self.tenancy,
                'code': self.code,
                'type': self.type,
                'description': self.description,
                'general ledger debit': self.general_ledger_debit,
                'general ledger credit': self.general_ledger_credit
                }

    def get_filtered_list(self, company_id):
        return self.objects.filter(tenancy=get_object_or_404(Tenancy, company_id=company_id))


class BaseComponent(TenancyDependentModel):
    """The base component represents a basic unit for a contract line.  In the case of a housing provider, this could
    for instance be one line specifying the rent price, and one line specifying any service costs.

    A base component always corresponds to a tenancy.
    """
    base_component_id = models.AutoField(primary_key=True)
    code = models.PositiveIntegerField()  # DESCRIPTION
    description = models.CharField(max_length=50)
    general_ledger_debit = models.CharField(max_length=10)
    general_ledger_credit = models.CharField(max_length=10)
    general_ledger_dimension = models.CharField(max_length=10)
    unit_id = models.CharField(max_length=10)

    def __str__(self):
        return self.tenancy.name + " - " + self.description

    def get_details(self):
        """Method to print all fields and their values."""
        return {'tenancy': self.tenancy,
                'code': self.code,
                'description': self.description,
                'general ledger debit': self.general_ledger_debit,
                'general ledger credit': self.general_ledger_credit,
                'general ledger dimension': self.general_ledger_dimension,
                'unit id': self.unit_id
                }


class VATRate(TenancyDependentModel):
    """The VAT rate defines the value added tax charged for a contract line.  In the Netherlands, there are three types
    of VAT: none (0%), low (9%), or high (21%).

    A VAT rate always corresponds to a tenancy.
    """
    vat_rate_id = models.AutoField(primary_key=True)
    type = models.PositiveIntegerField()
    description = models.CharField(max_length=30)
    start_date = models.DateField()
    end_date = models.DateField()
    percentage = models.FloatField()
    general_ledger_account = models.CharField(max_length=10)
    general_ledger_dimension = models.CharField(max_length=10)

    def __str__(self):
        return self.tenancy.name + " - " + self.description

    def get_details(self):
        """Method to print all fields and their values."""
        return {'tenancy': self.tenancy,
                'type': self.type,
                'description': self.description,
                'start date': self.start_date,
                'end date': self.end_date,
                'percentage': self.percentage,
                'general ledger account': self.general_ledger_account,
                'general ledger dimension': self.general_ledger_dimension
                }


class Contract(TenancyDependentModel):
    """The contract is an agreement between two parties (e.g. a company and a person).  In this case, the person(s)
    agree to pay some amount per some time period in exchange for a service or product.
    """
    MONTH = 'M'
    QUARTER = 'Q'
    HALF_YEAR = 'H'
    YEAR = 'Y'
    CUSTOM = 'V'
    INVOICING_PERIOD_CHOICES = [
        (MONTH, 'month'),
        (QUARTER, 'quarter'),
        (HALF_YEAR, 'half year'),
        (YEAR, 'year'),
        (CUSTOM, 'custom')
    ]

    PER_PERIOD = 'P'
    PER_DAY = 'D'  # Only possible if invoicing_period = 'V'
    INVOICING_AMOUNT_TYPE_CHOICES = [
        (PER_PERIOD, 'per period'),
        (PER_DAY, 'per day')
    ]

    contract_id = models.AutoField(primary_key=True)
    contract_type = models.ForeignKey(ContractType, on_delete=models.CASCADE)  # Ask if this should cascade
    status = models.CharField(max_length=1)
    invoicing_period = models.CharField(
        max_length=1,
        choices=INVOICING_PERIOD_CHOICES,
        default=MONTH
    )
    invoicing_amount_type = models.CharField(
        max_length=1,
        choices=INVOICING_AMOUNT_TYPE_CHOICES,
        default=PER_PERIOD
    )
    # Only not null if invoicing_type = PER_DAY
    invoicing_amount_of_days = models.PositiveSmallIntegerField(null=True, blank=True)
    # Only null if invoicing_type = PER_DAY
    invoicing_start_day = models.PositiveSmallIntegerField(null=True, blank=True)
    internal_customer_id = models.PositiveIntegerField()
    external_customer_id = models.PositiveIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    end_date_prolong = models.DateField()
    next_date_prolong = models.DateField()
    general_ledger_dimension_contract_1 = models.CharField(max_length=10)
    general_ledger_dimension_contract_2 = models.CharField(max_length=10)

    # Calculated fields
    balance = models.FloatField(default=0.0)
    base_amount = models.FloatField(default=0.0)
    vat_amount = models.FloatField(default=0.0)
    total_amount = models.FloatField(default=0.0)

    def __str__(self):
        return "Contact: " + self.tenancy.name + " - " + self.contract_type.description

    def get_components(self):
        return self.component_set.all()

    def get_contract_persons(self):
        return self.contractperson_set.all()

    def get_details(self):
        """Method to print all fields and their values."""
        return {'tenancy': self.tenancy,
                'contract type': self.contract_type,
                'status': self.status,
                'invoicing period': self.invoicing_period,
                'invoicing amount type': self.invoicing_amount_type,
                'invoicing amount of days': self.invoicing_amount_of_days,
                'invoicing start day': self.invoicing_start_day,
                'internal customer id': self.internal_customer_id,
                'external customer id': self.external_customer_id,
                'start date': self.start_date,
                'end date': self.end_date,
                'end date prolonging': self.end_date_prolong,
                'next date prolonging': self.next_date_prolong,
                'general ledger dimension 1': self.general_ledger_dimension_contract_1,
                'general ledger dimension 2': self.general_ledger_dimension_contract_2,
                'base amount': self.base_amount,
                'VAT amount': self.vat_amount,
                'total amount': self.total_amount,
                'balance': self.balance
                }

    def create_invoice(self, days_until_expiration, invoice_id, invoice_line_id):
        """Create an Invoice, then loop over all Components and call their create_invoice_line() method."""
        # Date will default to today, no need to set it
        invoice = Invoice(
            invoice_id=invoice_id,
            tenancy=self.tenancy,
            contract=self,
            internal_customer_id=5,
            external_customer_id=5,
            description=self.contract_type.description,
            base_amount=self.base_amount,
            vat_amount=self.vat_amount,
            total_amount=self.total_amount,
            balance=self.balance,
            expiration_date=datetime.date.today() + datetime.timedelta(days=days_until_expiration),
            invoice_number=0,
            general_ledger_account=0
        )
        components = self.component_set.select_related('vat_rate', 'base_component')
        invoice_lines = []
        for component in components:
            invoice_lines.append(component.create_invoice_line(invoice, invoice_line_id))
            invoice_line_id += 1

        return invoice, invoice_lines, invoice_line_id

    class Meta:
        constraints = [
            CheckConstraint(
                # If we have a custom invoicing period, then amount of days must be specified, and start day must not.
                # If we have a set invoicing period, then start day must be specified, and amount of days must not.
                name='check_period',
                check=Q(invoicing_period='V')
                & Q(invoicing_amount_of_days__isnull=False)
                & Q(invoicing_start_day__isnull=True)

                | (Q(invoicing_period='M')
                    | Q(invoicing_period='Q')
                    | Q(invoicing_period='H')
                    | Q(invoicing_period='Y')
                   )
                & Q(invoicing_amount_of_days__isnull=True)
                & Q(invoicing_start_day__isnull=False)
            ),
            CheckConstraint(
                name='contract_start_before_end',
                check=Q(end_date__gt=F('start_date'))
            )
        ]


class Component(TenancyDependentModel):
    """A Contract is built up of one or more components.  These 'contract lines' specify the amounts and services."""
    component_id = models.AutoField(primary_key=True)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)  # Ask if this should cascade
    base_component = models.ForeignKey(BaseComponent, on_delete=models.CASCADE)  # Ask if this should cascade
    vat_rate = models.ForeignKey(VATRate, on_delete=models.CASCADE)  # Ask if this should cascade
    description = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    end_date_prolong = models.DateField()
    next_date_prolong = models.DateField()
    invoice_number = models.FloatField()
    base_amount = models.FloatField()
    vat_amount = models.FloatField(default=0.0)
    total_amount = models.FloatField(default=0.0)
    unit_id = models.CharField(max_length=10)
    unit_amount = models.FloatField()

    def __str__(self):
        return "Component: " + self.description

    def create_invoice_line(self, invoice, invoice_line_id):
        return InvoiceLine(
            invoice_line_id=invoice_line_id,
            component=self,
            invoice=invoice,
            description=self.description,
            vat_type=self.vat_rate.type,
            base_amount=self.base_amount,
            vat_amount=self.vat_amount,
            total_amount=self.total_amount,
            invoice_number=self.invoice_number,
            general_ledger_account=0,
            general_ledger_dimension_base_component=self.base_component.general_ledger_dimension,
            general_ledger_dimension_contract_1=self.contract.general_ledger_dimension_contract_1,
            general_ledger_dimension_contract_2=self.contract.general_ledger_dimension_contract_2,
            general_ledger_dimension_vat=self.vat_rate.general_ledger_dimension,
            unit_price=self.unit_amount,
            unit_id=self.unit_id
        )

    class Meta:
        constraints = [
            CheckConstraint(
                check=Q(end_date__gt=F('start_date')),
                name='component_start_before_end'
            )
        ]


class ContractPerson(TenancyDependentModel):
    """A contract contains one or more contract persons."""
    AI = 'A'
    EMAIL = 'E'
    SMS = 'S'
    LETTER = 'L'
    INVOICE = 'I'

    PAYMENT_METHOD_CHOICES = [
        (AI, 'ai'),
        (EMAIL, 'email'),
        (SMS, 'sms'),
        (LETTER, 'letter'),
        (INVOICE, 'invoice')
    ]

    contract_person_id = models.AutoField(primary_key=True)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)  # Ask if this should cascade
    type = models.CharField(max_length=1)
    start_date = models.DateField()
    end_date = models.DateField()
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    payment_method = models.CharField(
        max_length=1,
        choices=PAYMENT_METHOD_CHOICES,
        default=INVOICE
    )
    iban = models.CharField(max_length=17)
    mandate = models.PositiveIntegerField()
    email = models.EmailField()
    percentage_of_total = models.PositiveIntegerField()
    payment_day = models.PositiveIntegerField()

    def __str__(self):
        return "contract person " + self.name


class Invoice(TenancyDependentModel):
    invoice_id = models.AutoField(primary_key=True)
    contract = models.OneToOneField(Contract, on_delete=models.CASCADE)  # Ask if this should cascade
    internal_customer_id = models.PositiveIntegerField()
    external_customer_id = models.PositiveIntegerField()
    description = models.CharField(max_length=50)
    base_amount = models.FloatField()
    vat_amount = models.FloatField(default=0.0)
    total_amount = models.FloatField(default=0.0)
    balance = models.FloatField(default=0.0)
    date = models.DateField(auto_now_add=True)
    expiration_date = models.DateField()
    invoice_number = models.PositiveIntegerField()
    general_ledger_account = models.CharField(max_length=10)

    def get_invoice_lines(self):
        return self.invoiceline_set.all()

    def get_details(self):
        """Method to print all fields and their values."""
        return {'internal customer id': self.internal_customer_id,
                'external customer id': self.external_customer_id,
                'description': self.description,
                'base amount': self.base_amount,
                'vat amount': self.vat_amount,
                'total amount': self.total_amount,
                'balance': self.balance,
                'date': self.date,
                'expiration date': self.expiration_date,
                'invoice number': self.invoice_number,
                'general ledger account': self.general_ledger_account,
                }


class InvoiceLine(models.Model):
    invoice_line_id = models.AutoField(primary_key=True)
    component = models.OneToOneField(Component, on_delete=models.CASCADE)  # Ask if this should cascade
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)  # Ask if this should cascade
    description = models.CharField(max_length=50)
    vat_type = models.PositiveIntegerField()
    base_amount = models.FloatField()
    vat_amount = models.FloatField(default=0.0)
    total_amount = models.FloatField(default=0.0)
    invoice_number = models.FloatField()
    general_ledger_account = models.CharField(max_length=10)
    general_ledger_dimension_base_component = models.CharField(max_length=10)
    general_ledger_dimension_contract_1 = models.CharField(max_length=10)
    general_ledger_dimension_contract_2 = models.CharField(max_length=10)
    general_ledger_dimension_vat = models.CharField(max_length=10)
    unit_price = models.FloatField()
    unit_id = models.CharField(max_length=10)
