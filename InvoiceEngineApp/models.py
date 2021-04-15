import datetime
from django.db import models, transaction
from django.db.models import F


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
    last_invoice_number = models.PositiveIntegerField(default=1)
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
        # Set the id for the next invoice. Take the highest id that is currently in the database and increment by 1
        next_invoice_id = 0
        next_invoice_line_id = 0
        next_collection_id = 0

        if Invoice.objects.exists():
            next_invoice_id = Invoice.objects.aggregate(models.Max('invoice_id')).get('invoice_id__max') + 1
            next_invoice_line_id = \
                InvoiceLine.objects.aggregate(models.Max('invoice_line_id')).get('invoice_line_id__max') + 1
            next_collection_id = Collection.objects.aggregate(models.Max('collection_id')).get('collection_id__max') + 1

        today = datetime.date.today()
        # Load all information about contracts that should be invoiced today or before today into memory
        contracts = list(
            self.contract_set.filter(
                next_date_prolong__lte=today
            ).order_by('contract_id').select_related('contract_type')
        )

        # Load all components into memory
        components = list(
            self.component_set.filter(
                next_date_prolong__lte=today
            ).order_by('contract_id').select_related('vat_rate', 'base_component')
        )
        amount_of_components = len(components)

        # Load all contract persons into memory
        contract_persons = list(
            self.contractperson_set.filter(
                contract__next_date_prolong__lte=today
            ).order_by('contract_id')
        )
        amount_of_contract_persons = len(contract_persons)

        # Prepare lists to store new objects for a single database query at the end of invoicing
        new_invoices = []
        new_invoice_lines = []
        new_collections = []
        # Create Invoices for all contracts
        for contract in contracts:
            # Debug print statement
            if next_invoice_id % 1000 == 0:
                print("contract no " + next_invoice_id.__str__())

            invoice = contract.create_invoice(self, next_invoice_id)
            self.last_invoice_number += 1

            # Create InvoiceLines for the components of this contract
            while amount_of_components > 0 and components[0].contract_id == contract.contract_id:
                component = components.pop(0)
                amount_of_components -= 1

                invoice_line = component.create_invoice_line(invoice, contract, next_invoice_line_id)

                next_invoice_line_id += 1
                new_invoice_lines.append(invoice_line)

            # Create Collections for the contract persons of this contract
            # This has to happen after creating the invoice lines, as they update the amounts on the invoice
            while amount_of_contract_persons > 0 and contract_persons[0].contract_id == contract.contract_id:
                contract_person = contract_persons.pop(0)
                amount_of_contract_persons -= 1

                collection = contract_person.create_collection(invoice, next_collection_id)

                next_collection_id += 1
                new_collections.append(collection)

            # The invoice is now finished (including all its InvoiceLines)
            # Update balance on the contract (using F is faster than +=)
            contract.balance = F('balance') + invoice.balance

            # Update next invoicing date on the contract
            month = contract.next_date_prolong.month
            year = contract.next_date_prolong.year
            day = contract.next_date_prolong.day
            if contract.invoicing_period == contract.MONTH:
                month += 1
            elif contract.invoicing_period == contract.QUARTER:
                month += 3
            elif contract.invoicing_period == contract.HALF_YEAR:
                month += 6
            elif contract.invoicing_period == contract.YEAR:
                year += 1

            # Shift year by one
            if month > 12:
                month %= 12
                year += 1

            if month == 2 and day > 28:
                # Correct for February & keep leap years into account
                # Note that there is no check for year % 100 == 0, which is not a leap year unless year % 400 == 0
                day = 29 if year % 4 == 0 else 28
            elif day == 31 and month in [4, 6, 9, 11]:
                # Correct for months that have 30 days
                day = 30

            contract.next_date_prolong = datetime.date(year=year, month=month, day=day)

            next_invoice_id += 1
            new_invoices.append(invoice)

        print("Received all new objects")
        print("Starting database transaction at " + datetime.datetime.now().__str__())
        # Save the changes made to the database in one transaction.  If one fails, they will all fail
        with transaction.atomic():
            print("Starting 'bulk update' of contracts at " + datetime.datetime.now().__str__())
            for contract in contracts:
                contract.save(
                    update_fields=['balance', 'next_date_prolong']
                )

            # Add all Invoices to the database with optimized bulk create
            # Do this before adding InvoiceLines, otherwise their foreign key pointing to an Invoice will fail
            print("Starting bulk create of invoices at " + datetime.datetime.now().__str__())
            Invoice.objects.bulk_create(new_invoices)
            print("Starting bulk create of collections at " + datetime.datetime.now().__str__())
            Collection.objects.bulk_create(new_collections)
            print("Starting bulk create of invoice lines at " + datetime.datetime.now().__str__())
            InvoiceLine.objects.bulk_create(new_invoice_lines)

            # Save the tenancy with the new last_invoice_number
            self.save(update_fields=['last_invoice_number'])


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
    end_date = models.DateField(null=True, blank=True)
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
    # Define options for invoicing period
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

    # Define options for the way the cost of a contract is calculated
    PER_PERIOD = 'P'
    PER_DAY = 'D'  # Only possible if invoicing_period = 'V'
    INVOICING_AMOUNT_TYPE_CHOICES = [
        (PER_PERIOD, 'per period'),
        (PER_DAY, 'per day')
    ]

    # Model fields
    contract_id = models.AutoField(primary_key=True)
    internal_customer_id = models.PositiveIntegerField()
    external_customer_id = models.PositiveIntegerField()

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

    # Dates
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    end_date_prolong = models.DateField(null=True, blank=True)
    next_date_prolong = models.DateField()

    # General ledger
    general_ledger_dimension_contract_1 = models.CharField(max_length=10)
    general_ledger_dimension_contract_2 = models.CharField(max_length=10)

    # Accumulated fields
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

    def create_invoice(self, tenancy, invoice_id):
        """Create an Invoice, then loop over all Components and call their create_invoice_line() method."""
        date_today = datetime.date.today()

        # Date will default to today, no need to set it.  No need to set amounts either
        return Invoice(
            invoice_id=invoice_id,
            tenancy=tenancy,
            contract=self,
            internal_customer_id=5,
            external_customer_id=5,
            description="Invoice: " + date_today.__str__(),
            expiration_date=date_today + datetime.timedelta(days=tenancy.days_until_invoice_expiration),
            invoice_number=tenancy.last_invoice_number,
            general_ledger_account=self.contract_type.general_ledger_debit,
            base_amount=self.base_amount,
            vat_amount=self.vat_amount,
            total_amount=self.total_amount,
            balance=self.total_amount
        )


class Component(TenancyDependentModel):
    """A Contract is built up of one or more components.  These 'contract lines' specify the amounts and services."""
    component_id = models.AutoField(primary_key=True)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)  # Ask if this should cascade
    base_component = models.ForeignKey(BaseComponent, on_delete=models.CASCADE)  # Ask if this should cascade
    vat_rate = models.ForeignKey(VATRate, on_delete=models.CASCADE)  # Ask if this should cascade
    description = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    end_date_prolong = models.DateField(null=True, blank=True)
    next_date_prolong = models.DateField()
    base_amount = models.FloatField(null=True)
    vat_amount = models.FloatField(default=0.0)
    total_amount = models.FloatField(default=0.0)
    unit_id = models.CharField(max_length=10, null=True)
    unit_amount = models.FloatField(null=True)
    number_of_units = models.FloatField(null=True)

    def __str__(self):
        return "Component: " + self.description

    def create_invoice_line(self, invoice, contract, invoice_line_id):
        return InvoiceLine(
            invoice_line_id=invoice_line_id,
            component=self,
            invoice=invoice,
            description=self.description,
            base_amount=self.base_amount,
            vat_amount=self.vat_amount,
            total_amount=self.total_amount,
            vat_type=self.vat_rate.type,

            general_ledger_account=self.base_component.general_ledger_credit,
            general_ledger_dimension_base_component=self.base_component.general_ledger_dimension,
            general_ledger_dimension_contract_1=contract.general_ledger_dimension_contract_1,
            general_ledger_dimension_contract_2=contract.general_ledger_dimension_contract_2,
            general_ledger_dimension_vat=self.vat_rate.general_ledger_dimension,

            number_of_units=self.number_of_units,
            unit_price=self.unit_amount,
            unit_id=self.unit_id
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
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)  # Ask if this should cascade
    type = models.CharField(max_length=1)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
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

    def create_collection(self, invoice, collection_id):
        return Collection(
            collection_id=collection_id,
            contract_person=self,
            invoice=invoice,
            payment_method=self.payment_method,
            payment_day=self.payment_day,
            mandate=self.mandate,
            iban=self.iban,
            amount=(self.percentage_of_total/100)*invoice.total_amount
        )


class Invoice(TenancyDependentModel):
    invoice_id = models.AutoField(primary_key=True)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)  # Ask if this should cascade
    internal_customer_id = models.PositiveIntegerField()
    external_customer_id = models.PositiveIntegerField()
    description = models.CharField(max_length=50)
    base_amount = models.FloatField(default=0.0)
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
    component = models.ForeignKey(Component, on_delete=models.CASCADE)  # Ask if this should cascade
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)  # Ask if this should cascade
    description = models.CharField(max_length=50)
    vat_type = models.PositiveIntegerField()
    base_amount = models.FloatField(null=True)
    vat_amount = models.FloatField(default=0.0)
    total_amount = models.FloatField(default=0.0)
    general_ledger_account = models.CharField(max_length=10)
    general_ledger_dimension_base_component = models.CharField(max_length=10)
    general_ledger_dimension_contract_1 = models.CharField(max_length=10)
    general_ledger_dimension_contract_2 = models.CharField(max_length=10)
    general_ledger_dimension_vat = models.CharField(max_length=10)
    unit_price = models.FloatField(null=True)
    unit_id = models.CharField(max_length=10, null=True)
    number_of_units = models.FloatField(null=True)


class Collection(models.Model):
    collection_id = models.AutoField(primary_key=True)
    contract_person = models.ForeignKey(ContractPerson, on_delete=models.CASCADE)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)  # Ask if this should cascade
    payment_method = models.CharField(max_length=1)
    payment_day = models.PositiveIntegerField()
    mandate = models.PositiveIntegerField()
    iban = models.CharField(max_length=17)
    amount = models.FloatField()
