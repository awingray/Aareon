import datetime
import random
from InvoiceEngineApp.models import (
    Tenancy,
    ContractType,
    VATRate,
    BaseComponent,
    Contract,
    Component,
    Invoice
)


def generate_benchmark_data():
    # We need:
    # 1 tenancy
    # 4 VAT rates
    # 10 contract types
    # 24 base components
    # 100 000 contracts with 1 - 10 contract lines each
    start_time = datetime.datetime.now()
    print("started populating db at " + start_time.__str__())

    tenancy = Tenancy.objects.create(
        tenancy_id=113582,
        day_next_prolong=datetime.date.today(),
        name='TestCorp'
    )

    contract_types = []
    for i in range(10):
        contract_types.append(
            ContractType.objects.create(
                tenancy=tenancy,
                general_ledger_debit='left',
                general_ledger_credit='right',
                code=5,
                type='G',
                description="test contract type " + i.__str__()
            )
        )

    base_components = []
    for i in range(24):
        base_components.append(
            BaseComponent.objects.create(
                tenancy=tenancy,
                code=15,
                description="test base component " + i.__str__(),
                general_ledger_debit='left',
                general_ledger_credit='right',
                general_ledger_dimension='dim',
                unit_id="twenty"
            )
        )

    vat_rates = []
    for i in range(4):
        vat_rates.append(
            VATRate.objects.create(
                tenancy=tenancy,
                type=29,
                description="test vat rate " + i.__str__(),
                start_date=datetime.date(2021, 1, 1),
                end_date=datetime.date(2022, 1, 1),
                percentage=i*10.5,
                general_ledger_account="acc",
                general_ledger_dimension="dim"
            )
        )

    contracts = []
    components = []
    for i in range(100000):
        if i % 1000 == 0:
            print("contract " + i.__str__())
        # amount_of_components = random.randint(1, max_components)
        amount_of_components = 1
        contract = Contract(
            contract_id=i,
            tenancy=tenancy,
            contract_type=random.choice(contract_types),
            status='S',
            invoicing_start_day=1,
            internal_customer_id=27,
            external_customer_id=5,
            start_date=datetime.date(2017, 5, 5),
            end_date=datetime.date(2022, 5, 5),
            end_date_prolong=datetime.date(2022, 5, 5),
            next_date_prolong=datetime.date(2021, 5, 5),
            general_ledger_dimension_contract_1="dim1",
            general_ledger_dimension_contract_2="dim2"
        )

        for j in range(amount_of_components):
            vat_rate = random.choice(vat_rates)

            base_amount = random.randint(100, 2000)
            vat_amount = base_amount*vat_rate.percentage
            total_amount = base_amount + vat_amount

            component = Component(
                component_id=i,  # This does not! work if amount_of_components != 1
                contract=contract,
                base_component=random.choice(base_components),
                vat_rate=vat_rate,
                description="test component " + j.__str__() + " of contract " + i.__str__(),
                start_date=datetime.date(2017, 5, 5),
                end_date=datetime.date(2022, 5, 5),
                end_date_prolong=datetime.date(2022, 5, 5),
                next_date_prolong=datetime.date(2021, 5, 5),
                invoice_number=i,
                base_amount=base_amount,
                vat_amount=vat_amount,
                total_amount=total_amount,
                unit_id="unitTc",
                unit_amount=200
            )

            contract.base_amount += base_amount
            contract.vat_amount += vat_amount
            contract.total_amount += total_amount
            contract.balance += total_amount
            contracts.append(contract)
            components.append(component)

    print("start adding contracts & components to db")
    Contract.objects.bulk_create(contracts)
    Component.objects.bulk_create(components)
    print("done")

    end_time = datetime.datetime.now()
    print("started populating db at " + start_time.__str__())
    print("ended populating db at " + end_time.__str__())


def clear_database():
    # This works only if on_delete=CASCADE is set for every dependent model
    print("started clearing db at " + datetime.datetime.now().__str__())
    Tenancy.objects.all().delete()
    print("ended clearing db at " + datetime.datetime.now().__str__())


def clear_invoices():
    # This method removes all invoices and invoice lines from the database
    print("started clearing invoices at " + datetime.datetime.now().__str__())
    Invoice.objects.all().delete()
    print("ended clearing invoices at " + datetime.datetime.now().__str__())


def run_invoice_engine():
    # Get the testing tenancy and invoice their contracts
    tenancy = Tenancy.objects.get(tenancy_id=113582)

    start_time = datetime.datetime.now()
    print("started invoicing at " + start_time.__str__())

    tenancy.invoice_contracts()

    end_time = datetime.datetime.now()
    print("ended invoicing at " + end_time.__str__())
