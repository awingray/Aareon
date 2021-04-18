import datetime
import random
from InvoiceEngineApp.models import (
    Tenancy,
    ContractType,
    VATRate,
    BaseComponent,
    Contract,
    Component,
    Invoice,
    ContractPerson
)


def generate_benchmark_data(max_components):
    # We need:
    # 1 tenancy
    # 4 VAT rates
    # 10 contract types
    # 24 base components
    # 100 000 contracts with 1 - max_components contract lines each & 1 - 2 contract persons
    start_time = datetime.datetime.now()
    print("started populating db at " + start_time.__str__())

    amount_of_contract_types = 10
    amount_of_base_components = 24
    amount_of_vat_rates = 4
    amount_of_contracts = 20000
    max_contract_persons = 2

    tenancy = Tenancy.objects.create(
        tenancy_id=113582,
        day_next_prolong=datetime.date.today(),
        name='TestCorp',
        days_until_invoice_expiration=14,
        number_of_contracts=amount_of_contracts
    )

    contract_types = []
    for i in range(amount_of_contract_types):
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
    for i in range(amount_of_base_components):
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
    for i in range(amount_of_vat_rates):
        vat_rates.append(
            VATRate.objects.create(
                tenancy=tenancy,
                type=29,
                description="test vat rate " + i.__str__(),
                start_date=datetime.date(2021, 1, 1),
                percentage=(i*10.5) % 100,
                general_ledger_account="acc",
                general_ledger_dimension="dim"
            )
        )

    contracts = []
    components = []
    contract_persons = []
    total_components = 0
    total_contract_persons = 0
    for i in range(amount_of_contracts):
        if i % 1000 == 0:
            print("contract " + i.__str__())
        amount_of_components = random.randint(1, max_components)
        amount_of_contract_persons = random.randint(1, max_contract_persons)
        contract = Contract(
            contract_id=i,
            tenancy=tenancy,
            contract_type=random.choice(contract_types),
            status='S',
            invoicing_start_day=1,
            internal_customer_id=27,
            external_customer_id=5,
            start_date=datetime.date(2017, 5, 5),
            next_date_prolong=datetime.date(2021, 4, 6),
            general_ledger_dimension_contract_1="dim1",
            general_ledger_dimension_contract_2="dim2"
        )

        for j in range(amount_of_components):
            vat_rate = random.choice(vat_rates)

            base_amount = random.randint(100, 2000)
            vat_amount = base_amount*vat_rate.percentage/100
            total_amount = base_amount + vat_amount

            component = Component(
                component_id=total_components,
                tenancy=tenancy,
                contract=contract,
                base_component=random.choice(base_components),
                vat_rate=vat_rate,
                description="test component " + j.__str__() + " of contract " + i.__str__(),
                start_date=datetime.date(2017, 5, 5),
                next_date_prolong=datetime.date(2021, 4, 6),
                base_amount=base_amount,
                vat_amount=vat_amount,
                total_amount=total_amount,
            )

            contract.total_amount += total_amount
            contract.base_amount += base_amount
            contract.vat_amount += vat_amount

            components.append(component)
            total_components += 1

        for k in range(amount_of_contract_persons):
            contract_person = ContractPerson(
                contract_person_id=total_contract_persons,
                tenancy=tenancy,
                contract=contract,
                type='P',
                start_date=datetime.date(2017, 5, 5),
                name='A. Lee',
                address='Nijenborgh 4',
                city='Groningen',
                payment_method=ContractPerson.DIRECT_DEBIT,
                iban='INGB 55598875',
                mandate=555884,
                email='random@randommail.org',
                percentage_of_total=100/amount_of_contract_persons,
                payment_day=5
            )
            contract_persons.append(contract_person)
            total_contract_persons += 1

        contracts.append(contract)

    print("start adding contracts & components & contract persons to db")
    Contract.objects.bulk_create(contracts)
    print("Contracts done, starting components")
    Component.objects.bulk_create(components)
    print("components done, starting contract persons")
    ContractPerson.objects.bulk_create(contract_persons)
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
    invoicing_time = end_time - start_time
    print("Done")
    print("started invoicing at " + start_time.__str__())
    print("ended invoicing at " + end_time.__str__())
    print("invoicing time was " + invoicing_time.__str__())
