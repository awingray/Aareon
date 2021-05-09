import datetime
from django.db import models, transaction
import csv
from django.http import HttpResponse


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
    date_next_prolongation = models.DateField(null=True, blank=True)
    days_until_invoice_expiration = models.PositiveSmallIntegerField(default=14)

    def __str__(self):
        return self.name

    def get_details(self):
        """Method to print all fields and their values."""
        return {
            "name": self.name,
            "number of contracts": self.number_of_contracts,
            "last invoice number": self.last_invoice_number,
            "date of next prolonging": self.date_next_prolongation,
            "days until invoice expiration": self.days_until_invoice_expiration,
        }

    def invoice_contracts(self):
        # Set the id for the next object.  Take the highest id that is currently in the database and increment by 1
        next_invoice_id = 0
        next_invoice_line_id = 0

        if Invoice.objects.exists():
            next_invoice_id = (
                Invoice.objects.aggregate(models.Max("invoice_id")).get(
                    "invoice_id__max"
                )
                + 1
            )
            next_invoice_line_id = (
                InvoiceLine.objects.aggregate(models.Max("invoice_line_id")).get(
                    "invoice_line_id__max"
                )
                + 1
            )

        date_today = datetime.date.today()

        # Load all components into memory
        components = list(
            self.component_set.filter(
                date_next_prolongation__isnull=False,
                date_next_prolongation__lte=date_today,
            )
            .order_by("contract_id")
            .select_related("contract__contract_type", "vat_rate", "base_component")
        )

        if not components:
            # There are no contracts to prolong
            return

        # Load all contract persons into memory
        contract_persons = list(
            self.contractperson_set.filter(
                contract__date_next_prolongation__isnull=False,
                contract__date_next_prolongation__lte=date_today,
            ).order_by("contract_id")
        )

        new_invoices = []
        new_invoice_lines = []
        new_gl_posts = []
        new_collections = []

        invoice = components[0].contract.invoice(date_today, next_invoice_id, self)
        new_invoices.append(invoice)
        next_invoice_id += 1

        previous_contract = components[0].contract_id

        for component in components:
            # Create a new invoice only when a new contract is reached
            # This is possible because components are ordered by contract_id
            if component.contract_id != previous_contract:
                # Invoice for contract x is finished, generate collections for contract x
                while (
                    contract_persons
                    and contract_persons[0].contract_id == previous_contract
                ):
                    contract_persons[0].invoice(self, invoice, new_collections)
                    contract_persons.pop(0)

                invoice.create_gl_post(new_gl_posts)

                # Create an invoice for the new contract
                invoice = component.contract.invoice(date_today, next_invoice_id, self)
                new_invoices.append(invoice)
                next_invoice_id += 1

            component.invoice(
                next_invoice_line_id, invoice, new_invoice_lines, new_gl_posts
            )
            next_invoice_line_id += 1
            previous_contract = component.contract_id

        print("Received all new objects")
        print("Starting database transaction at " + datetime.datetime.now().__str__())
        # Save the changes made to the database in one transaction.  If one fails, they will all fail
        with transaction.atomic():
            print(
                "Starting 'bulk update' of components & contracts at "
                + datetime.datetime.now().__str__()
            )
            previous_contract = -1
            for component in components:
                if component.contract_id != previous_contract:
                    component.contract.save(
                        update_fields=[
                            "balance",
                            "date_next_prolongation",
                            "date_prolonged_until",
                        ]
                    )

                component.save(
                    update_fields=["date_next_prolongation", "date_prolonged_until"]
                )
                previous_contract = component.contract_id

            # Add all Invoices to the database with optimized bulk create
            # Do this before adding InvoiceLines, otherwise their foreign key pointing to an Invoice will fail
            print(
                "Starting bulk create of invoices at "
                + datetime.datetime.now().__str__()
            )
            Invoice.objects.bulk_create(new_invoices)
            print(
                "Starting bulk create of invoice lines at "
                + datetime.datetime.now().__str__()
            )
            InvoiceLine.objects.bulk_create(new_invoice_lines)
            print(
                "Starting bulk create of general ledger posts at "
                + datetime.datetime.now().__str__()
            )
            GeneralLedgerPost.objects.bulk_create(new_gl_posts)
            print(
                "Starting bulk create of collections at "
                + datetime.datetime.now().__str__()
            )
            Collection.objects.bulk_create(new_collections)

            # Save the tenancy with the new last_invoice_number
            self.save(update_fields=["last_invoice_number"])


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
        return {
            "tenancy": self.tenancy,
            "code": self.code,
            "type": self.type,
            "description": self.description,
            "general ledger debit": self.general_ledger_debit,
            "general ledger credit": self.general_ledger_credit,
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
    unit_id = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return (
            self.description + " - unit " + self.unit_id.__str__()
            if self.unit_id
            else self.description
        )

    def get_details(self):
        """Method to print all fields and their values."""
        return {
            "tenancy": self.tenancy,
            "code": self.code,
            "description": self.description,
            "general ledger debit": self.general_ledger_debit,
            "general ledger credit": self.general_ledger_credit,
            "general ledger dimension": self.general_ledger_dimension,
            "unit id": self.unit_id,
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
        return (
            "Type "
            + self.type.__str__()
            + ": "
            + self.description
            + " - "
            + self.percentage.__str__()
            + "%"
        )

    def get_details(self):
        """Method to print all fields and their values."""
        return {
            "tenancy": self.tenancy,
            "type": self.type,
            "description": self.description,
            "start date": self.start_date,
            "end date": self.end_date,
            "percentage": self.percentage,
            "general ledger account": self.general_ledger_account,
            "general ledger dimension": self.general_ledger_dimension,
        }


class Contract(TenancyDependentModel):
    """The contract is an agreement between two parties (e.g. a company and a person).  In this case, the person(s)
    agree to pay some amount per some time period in exchange for a service or product.
    """

    # Define options for invoicing period
    MONTH = "M"
    QUARTER = "Q"
    HALF_YEAR = "H"
    YEAR = "Y"
    CUSTOM = "V"
    INVOICING_PERIOD_CHOICES = [
        (MONTH, "Month"),
        (QUARTER, "Quarter"),
        (HALF_YEAR, "Half year"),
        (YEAR, "Year"),
        (CUSTOM, "Custom"),
    ]

    # Define options for the way the cost of a contract is calculated
    PER_PERIOD = "P"
    PER_DAY = "D"  # Only possible if invoicing_period = 'V'
    INVOICING_AMOUNT_TYPE_CHOICES = [(PER_PERIOD, "per period"), (PER_DAY, "per day")]

    # Model fields
    contract_id = models.AutoField(primary_key=True)
    external_customer_id = models.PositiveIntegerField()

    contract_type = models.ForeignKey(ContractType, on_delete=models.CASCADE)
    status = models.CharField(max_length=1)
    invoicing_period = models.CharField(
        max_length=1, choices=INVOICING_PERIOD_CHOICES, default=MONTH
    )
    invoicing_amount_type = models.CharField(
        max_length=1, choices=INVOICING_AMOUNT_TYPE_CHOICES, default=PER_PERIOD
    )
    # Only not null if invoicing_type = PER_DAY
    invoicing_amount_of_days = models.PositiveSmallIntegerField(null=True, blank=True)
    # Only null if invoicing_type = PER_DAY
    invoicing_start_day = models.PositiveSmallIntegerField(null=True, blank=True)

    # Dates
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    date_prolonged_until = models.DateField(null=True, blank=True)
    date_next_prolongation = models.DateField(null=True)

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

    def get_invoices(self):
        return self.invoice_set.all()

    def get_period(self):
        for key, value in self.INVOICING_PERIOD_CHOICES:
            if key == self.invoicing_period:
                return value

    def get_details(self):
        """Method to print all fields and their values."""
        return {
            "tenancy": self.tenancy,
            "contract type": self.contract_type,
            "status": self.status,
            "invoicing period": self.invoicing_period,
            "invoicing amount type": self.invoicing_amount_type,
            "invoicing amount of days": self.invoicing_amount_of_days,
            "invoicing start day": self.invoicing_start_day,
            "external customer id": self.external_customer_id,
            "start date": self.start_date,
            "end date": self.end_date,
            "end date prolonging": self.date_prolonged_until,
            "next date prolonging": self.date_next_prolongation,
            "general ledger dimension 1": self.general_ledger_dimension_contract_1,
            "general ledger dimension 2": self.general_ledger_dimension_contract_2,
            "base amount": self.base_amount,
            "VAT amount": self.vat_amount,
            "total amount": self.total_amount,
            "balance": self.balance,
        }

    def compute_date_next_prolongation(self, previous_date):
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

        # Shift year by one if the 12th month is passed
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

        return datetime.date(year, month, day)

    def invoice(self, date_today, next_id, tenancy):
        # Set the new prolongation date and the date until which the contract is prolonged
        if self.end_date < self.date_next_prolongation:
            # The contract ended during the previous invoicing period, so definitively end it
            self.date_next_prolongation = None
            self.date_prolonged_until = self.end_date
        else:
            self.date_prolonged_until = self.date_next_prolongation
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
            expiration_date=date_today
            + datetime.timedelta(days=tenancy.days_until_invoice_expiration),
            invoice_number=tenancy.last_invoice_number,
            general_ledger_account=self.contract_type.general_ledger_debit,
        )

    """ This function is used to make sure the aggregate "percentage" doesn't exceed 100 """

    def validate(self):
        return (
            self.contractperson_set.aggregate(models.Sum("percentage_of_total")).get(
                "percentage_of_total__sum"
            )
            if self.contractperson_set.exists()
            else 0
        )


class Component(TenancyDependentModel):
    """A Contract is built up of one or more components.  These 'contract lines' specify the amounts and services."""

    component_id = models.AutoField(primary_key=True)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    base_component = models.ForeignKey(BaseComponent, on_delete=models.CASCADE)
    vat_rate = models.ForeignKey(VATRate, null=True, on_delete=models.CASCADE)
    description = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    date_prolonged_until = models.DateField(null=True, blank=True)
    date_next_prolongation = models.DateField()
    base_amount = models.FloatField(null=True, blank=True)
    vat_amount = models.FloatField(default=0.0)
    total_amount = models.FloatField(default=0.0)
    unit_id = models.CharField(max_length=10, null=True, blank=True)
    unit_amount = models.FloatField(null=True, blank=True)
    number_of_units = models.FloatField(null=True, blank=True)

    def __str__(self):
        return "Component: " + self.description

    def create_invoice_lines(
        self,
        next_id,
        invoice,
        base_amount,
        vat_amount,
        total_amount,
        unit_amount,
        new_invoice_lines,
        new_gl_posts,
    ):
        invoice_line = InvoiceLine(
            invoice_line_id=next_id,
            component=self,
            invoice=invoice,
            description=self.description,
            base_amount=base_amount,
            vat_amount=vat_amount,
            total_amount=total_amount,
            vat_type=self.vat_rate.type,
            general_ledger_account=self.base_component.general_ledger_credit,
            general_ledger_dimension_base_component=self.base_component.general_ledger_dimension,
            general_ledger_dimension_contract_1=self.contract.general_ledger_dimension_contract_1,
            general_ledger_dimension_contract_2=self.contract.general_ledger_dimension_contract_2,
            general_ledger_dimension_vat=self.vat_rate.general_ledger_dimension,
            number_of_units=self.number_of_units,
            unit_price=unit_amount,
            unit_id=self.unit_id,
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
        base_amount = self.base_amount
        vat_amount = self.vat_amount
        total_amount = self.total_amount
        unit_amount = self.unit_amount

        if self.end_date < self.date_next_prolongation:
            # The component ended during the previous invoicing period, so correct the costs for the amount of days
            days_in_period = (
                self.date_next_prolongation - self.date_prolonged_until
            ).days
            days_to_invoice = (self.end_date - self.date_prolonged_until).days

            base_amount = base_amount / days_in_period * days_to_invoice
            vat_amount = vat_amount / days_in_period * days_to_invoice
            total_amount = total_amount / days_in_period * days_to_invoice
            unit_amount = unit_amount / days_in_period * days_to_invoice

            # Definitively end this component by setting date_next_prolongation to None
            self.date_next_prolongation = None
            self.date_prolonged_until = self.end_date
        else:
            self.date_prolonged_until = self.date_next_prolongation
            self.date_next_prolongation = self.contract.compute_date_next_prolongation(
                self.date_next_prolongation
            )

        self.create_invoice_lines(
            next_id,
            invoice,
            base_amount,
            vat_amount,
            total_amount,
            unit_amount,
            new_invoice_lines,
            new_gl_posts,
        )


class ContractPerson(TenancyDependentModel):
    """A contract contains one or more contract persons."""

    DIRECT_DEBIT = "D"
    EMAIL = "E"
    SMS = "S"
    LETTER = "L"
    INVOICE = "I"

    PAYMENT_METHOD_CHOICES = [
        (DIRECT_DEBIT, "direct debit"),
        (EMAIL, "email"),
        (SMS, "sms"),
        (LETTER, "letter"),
        (INVOICE, "invoice"),
    ]

    contract_person_id = models.AutoField(primary_key=True)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    type = models.CharField(max_length=1)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    payment_method = models.CharField(
        max_length=1, choices=PAYMENT_METHOD_CHOICES, default=INVOICE
    )
    iban = models.CharField(max_length=17, null=True, blank=True)
    mandate = models.PositiveIntegerField(null=True, blank=True)
    email = models.EmailField()
    percentage_of_total = models.PositiveIntegerField()
    payment_day = models.PositiveIntegerField()

    def __str__(self):
        return "contract person " + self.name

    def get_details(self):
        return {
            "name": self.name,
            "address": self.address,
            "city": self.city,
            "payment_method": self.payment_method,
            "payment_day": self.payment_day,
            "contract_person_id": self.contract_person_id,
            "mandate": self.mandate,
            "iban": self.iban,
            "email": self.email,
        }

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
                amount=(self.percentage_of_total / 100) * invoice.total_amount,
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
    general_ledger_account = models.CharField(max_length=10)

    def get_invoice_lines(self):
        return self.invoiceline_set.all()

    def get_details(self):
        """Method to print all fields and their values."""
        return {
            "external customer id": self.external_customer_id,
            "description": self.description,
            "base amount": self.base_amount,
            "vat amount": self.vat_amount,
            "total amount": self.total_amount,
            "balance": self.balance,
            "date": self.date,
            "expiration date": self.expiration_date,
            "invoice number": self.invoice_number,
            "general ledger account": self.general_ledger_account,
        }

    def create_gl_post(self, new_gl_posts):
        new_gl_posts.append(
            GeneralLedgerPost(
                tenancy=self.tenancy,
                invoice=self,
                invoice_line=None,
                date=self.date,
                general_ledger_account=self.general_ledger_account,
                general_ledger_dimension_base_component=None,
                general_ledger_dimension_contract_1=self.contract.general_ledger_dimension_contract_1,
                general_ledger_dimension_contract_2=self.contract.general_ledger_dimension_contract_2,
                general_ledger_dimension_vat=None,
                description="Debtors",
                amount_debit=self.total_amount,
                amount_credit=0.0,
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
    general_ledger_account = models.CharField(max_length=10)
    general_ledger_dimension_base_component = models.CharField(max_length=10)
    general_ledger_dimension_contract_1 = models.CharField(max_length=10)
    general_ledger_dimension_contract_2 = models.CharField(max_length=10)
    general_ledger_dimension_vat = models.CharField(max_length=10, null=True)
    unit_price = models.FloatField(null=True)
    unit_id = models.CharField(max_length=10, null=True)
    number_of_units = models.FloatField(null=True)

    def create_gl_posts(self, new_gl_posts):
        new_gl_posts.append(
            GeneralLedgerPost(
                tenancy=self.invoice.tenancy,
                invoice=None,  # This could be changed to invoice in needed
                invoice_line=self,
                date=self.invoice.date,
                general_ledger_account=self.general_ledger_account,
                general_ledger_dimension_base_component=self.general_ledger_dimension_base_component,
                general_ledger_dimension_contract_1=self.general_ledger_dimension_contract_1,
                general_ledger_dimension_contract_2=self.general_ledger_dimension_contract_2,
                general_ledger_dimension_vat=None,
                description="Proceeds",
                amount_credit=self.base_amount,
                amount_debit=0.0,
            )
        )

        # Only create a post for the general ledger for the VAT if VAT is applicable
        if self.vat_type:
            new_gl_posts.append(
                GeneralLedgerPost(
                    tenancy=self.invoice.tenancy,
                    invoice=None,
                    invoice_line=self,
                    date=self.invoice.date,
                    general_ledger_account=self.component.vat_rate.general_ledger_account,
                    general_ledger_dimension_base_component=self.general_ledger_dimension_base_component,
                    general_ledger_dimension_contract_1=self.general_ledger_dimension_contract_1,
                    general_ledger_dimension_contract_2=self.general_ledger_dimension_contract_2,
                    general_ledger_dimension_vat=self.general_ledger_dimension_vat,
                    description="VAT",
                    amount_credit=self.vat_amount,
                    amount_debit=0.0,
                )
            )


class Collection(TenancyDependentModel):
    contract_person = models.ForeignKey(ContractPerson, on_delete=models.CASCADE)
    # Ask if this should cascade
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=1)
    payment_day = models.PositiveIntegerField()
    mandate = models.PositiveIntegerField()
    iban = models.CharField(max_length=17)
    amount = models.FloatField(default=0.0)


class GeneralLedgerPost(TenancyDependentModel):
    invoice = models.ForeignKey(Invoice, null=True, on_delete=models.CASCADE)
    invoice_line = models.ForeignKey(InvoiceLine, null=True, on_delete=models.CASCADE)
    date = models.DateField()
    general_ledger_account = models.CharField(max_length=10)
    general_ledger_dimension_base_component = models.CharField(null=True, max_length=10)
    general_ledger_dimension_contract_1 = models.CharField(max_length=10)
    general_ledger_dimension_contract_2 = models.CharField(max_length=10)
    general_ledger_dimension_vat = models.CharField(null=True, max_length=10)
    description = models.CharField(max_length=30)
    amount_debit = models.FloatField()
    amount_credit = models.FloatField()
