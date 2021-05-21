import datetime as dt
import decimal as dc

from django.test import TestCase
from InvoiceEngineApp.models import Contract
from model_bakery import baker


class ComponentMethodsTest(TestCase):
    def setUp(self):
        self.component = baker.make(
            'Component',
            contract__invoicing_period=Contract.MONTH,
            contract__start_date=dt.date(2020, 1, 1),
            contract__end_date=None,
            contract__date_next_prolongation=dt.date(2021, 5, 1),
            contract__date_prev_prolongation=dt.date(2021, 4, 1),
            vat_rate__percentage=dc.Decimal(20),
            date_next_prolongation=dt.date(2021, 5, 1),
            date_prev_prolongation=dt.date(2021, 4, 1),
            start_date=dt.date(2020, 1, 1),
            end_date=dt.date(2021, 4, 1),
            base_amount=dc.Decimal(50),
            vat_amount=dc.Decimal(10),
            total_amount=dc.Decimal(60),
            unit_id=None,
            unit_amount=None,
            number_of_units=None
        )

    def test_get_amounts_between_dates(self):
        """Method to test the get_amounts_between_dates() method of
        the Component class.
        """
        # Get the costs for 9 days of February and 12 days of March
        base, vat, total, unit = self.component.get_amounts_between_dates(
            dt.date(2021, 2, 20),
            dt.date(2021, 3, 13)
        )
        self.assertEqual(base, dc.Decimal('16.07') + dc.Decimal('19.35'))
        self.assertEqual(vat, dc.Decimal('3.21') + dc.Decimal('3.87'))
        self.assertEqual(total, dc.Decimal('42.50'))
        self.assertEqual(unit, 0)

        # Test 4 full periods
        base, vat, total, unit = self.component.get_amounts_between_dates(
            dt.date(2020, 1, 1),
            dt.date(2020, 5, 1)
        )
        self.assertEqual(base, 200)
        self.assertEqual(vat, 40)
        self.assertEqual(total, 240)
        self.assertEqual(unit, 0)

        # Test with a quarter
        # 57 days of period 1, all of period 2, 8 days of period 3
        # 91 days in period 1, 91 days in period 2, 92 days in period 3
        self.component.contract.invoicing_period = Contract.QUARTER
        base, vat, total, unit = self.component.get_amounts_between_dates(
            dt.date(2020, 2, 4),
            dt.date(2020, 7, 9)
        )
        self.assertEqual(base, dc.Decimal('31.32') + 50 + dc.Decimal('4.35'))
        self.assertEqual(vat, dc.Decimal('6.26') + 10 + dc.Decimal('0.87'))
        self.assertEqual(total, dc.Decimal('102.8'))
        self.assertEqual(unit, 0)

        # Test with unit amount instead of base
        self.component.base_amount = None
        self.component.unit_amount = dc.Decimal(30)
        self.component.number_of_units = 5
        self.component.vat_amount = 30
        self.component.unit_id = "102"
        base, vat, total, unit = self.component.get_amounts_between_dates(
            dt.date(2020, 2, 4),
            dt.date(2020, 7, 9)
        )
        self.assertEqual(base, 0)
        self.assertEqual(vat, dc.Decimal('18.79') + 30 + dc.Decimal('2.61'))
        self.assertEqual(total, dc.Decimal('308.4'))
        self.assertEqual(unit, dc.Decimal('18.79') + 30 + dc.Decimal('2.61'))
