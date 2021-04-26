from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings
import datetime
from InvoiceEngineApp.models import *
from model_bakery import baker


class TenancyTest(TestCase):
    def setUp(self):
        self.tenancy = baker.make(Tenancy)
        self.name = str(self.tenancy)

    def test_creation(self):
        # print(self.tenancy.get_details())
        self.assertEqual(self.name, str(self.tenancy))
        self.assertIsNone(self.tenancy.day_next_prolong)
        self.assertEqual(Tenancy.objects.all().count(), 1)
        self.assertEqual(self.tenancy.days_until_invoice_expiration, 14)
        self.assertEqual(self.tenancy.number_of_contracts, 0)
        self.assertEqual(self.tenancy.last_invoice_number, 1)

    def test_invoice_contracts(self):
        pass


class VATRateTest(TestCase):
    def setUp(self):
        self.vatrate = baker.make(VATRate)

    def test_creation(self):
        # print(self.vatrate.get_details())
        self.assertEqual(VATRate.objects.all().count(), 1)


class ContractTypeTest(TestCase):
    def setUp(self):
        self.contracttype = baker.make(ContractType)

    def test_creation(self):
        # print(self.contracttype.get_details())
        self.assertEqual(ContractType.objects.all().count(), 1)


class BaseComponentTest(TestCase):
    def setUp(self):
        self.base_component = baker.make(BaseComponent)

    def test_creation(self):
        # print(self.base_component.get_details())
        self.assertEqual(BaseComponent.objects.all().count(), 1)


class ContractTest(TestCase):
    def setUp(self):
        self.contract = baker.make(Contract)

    def test_creation(self):
        print()
        self.assertEqual(Contract.objects.all().count(), 1)


class ComponentTest(TestCase):
    def setUp(self):
        self.component = baker.make(Component)

    def test_creation(self):
        # print(self.component.get_details())
        self.assertEqual(Component.objects.all().count(), 1)


class ContractPersonTest(TestCase):
    def setUp(self):
        self.contract_person = baker.make(ContractPerson, _quantity=3)

    def test_creation(self):
        self.assertEqual(ContractPerson.objects.all().count(), 3)


class InvoiceTest(TestCase):
    def setUp(self):
        self.invoice = baker.make(Invoice)

    def test_creation(self):
        # print(self.invoice.get_details())
        self.assertEqual(Invoice.objects.all().count(), 1)


class InvoiceLineTest(TestCase):
    def setUp(self):
        self.invoice_line = baker.make(InvoiceLine)

    def test_creation(self):
        # print(self.invoice_line.get_details())
        self.assertEqual(InvoiceLine.objects.all().count(), 1)
