from django.db import models


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

    def __str__(self):
        return self.name

    def get_details(self):
        """Method to print all fields and their values."""
        return {'name': self.name,
                'number of contracts': self.number_of_contracts,
                'last invoice number': self.last_invoice_number,
                'date of next prolonging': self.day_next_prolong
                }


class ContractType(models.Model):
    """A company may have contracts for different services, for instance a housing provider which has different
    contracts for different types of apartments, parking spaces, garages, etc.

    A contract type always corresponds to a tenancy.
    """
    contract_type_id = models.AutoField(primary_key=True)
    tenancy = models.ForeignKey(Tenancy, on_delete=models.CASCADE)  # Ask if this should cascade
    code = models.PositiveIntegerField()
    type = models.CharField(max_length=1)
    description = models.CharField(max_length=50)
    general_ledger_debit = models.CharField(max_length=10)
    general_ledger_credit = models.CharField(max_length=10)

    def __str__(self):
        return self.tenancy.name + " - " + self.description

    def get_details(self):
        """Method to print all fields and their values."""
        return {'tenancy': self.tenancy,
                'code': self.code,
                'type': self.type,
                'description': self.description,
                'general ledger debit': self.general_ledger_debit,
                'general ledger credit': self.general_ledger_credit
                }


class BaseComponent(models.Model):
    """The base component represents a basic unit for a contract line.  In the case of a housing provider, this could
    for instance be one line specifying the rent price, and one line specifying any service costs.

    A base component always corresponds to a tenancy.
    """
    base_component_id = models.AutoField(primary_key=True)
    tenancy = models.ForeignKey(Tenancy, on_delete=models.CASCADE)  # Ask if this should cascade
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


class VATRate(models.Model):
    """The VAT rate defines the value added tax charged for a contract line.  In the Netherlands, there are three types
    of VAT: none (0%), low (9%), or high (21%).

    A VAT rate always corresponds to a tenancy.
    """
    vat_rate_id = models.AutoField(primary_key=True)
    tenancy = models.ForeignKey(Tenancy, on_delete=models.CASCADE)  # Ask if this should cascade
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
