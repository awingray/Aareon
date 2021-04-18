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
        print(self.tenancy.get_details())
        self.assertEqual(self.name, str(self.tenancy))
        self.assertEqual(datetime.date.today(), self.tenancy.day_next_prolong)
        self.assertEqual(Tenancy.objects.all().count(), 1)
        self.assertEqual(self.tenancy.days_until_invoice_expiration, 14)
        self.assertEqual(self.tenancy.number_of_contracts, 0)
        self.assertEqual(self.tenancy.last_invoice_number, 0)


class VATRateTest(TestCase):
    def setUp(self):
        self.vatrate = baker.make(VATRate)

    def test_creation(self):
        print(self.vatrate.get_details())
        self.assertEqual(VATRate.objects.all().count(), 1)


class ContractTypeTest(TestCase):
    def setUp(self):
        self.contracttype = baker.make(ContractType)

    def test_creation(self):
        print(self.contracttype.get_details())
        self.assertEqual(ContractType.objects.all().count(), 1)


class ContractTest(TestCase):
    def setUp(self):
        self.contract = baker.make(Contract)

    def test_creation(self):
        print(self.contract.get_details())
        self.assertEqual(ContractType.objects.all().count(), 1)


class BaseComponentTest(TestCase):
    def setUp(self):
        self.base_component = baker.make(BaseComponent)

    def test_creation(self):
        print(self.base_component.get_details())
        self.assertEqual(BaseComponent.objects.all().count(), 1)
