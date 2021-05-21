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
            contract__start_date=dt.date(2021, 1, 1),
            contract__end_date=None,
            contract__date_next_prolongation=dt.date(2021, 5, 1),
            contract__date_prev_prolongation=dt.date(2021, 4, 1),
            vat_rate__percentage=dc.Decimal(21),
            date_next_prolongation=dt.date(2021, 5, 1),
            date_prev_prolongation=dt.date(2021, 4, 1),
            start_date=dt.date(2021, 1, 1),
            end_date=dt.date(2021, 4, 1),
            base_amount=dc.Decimal(50),
            vat_amount=dc.Decimal(10),
            total_amount=dc.Decimal(60),
            unit_id=None,
            unit_amount=None,
            number_of_units=None
        )

    def test_get_amounts_between_dates(self):
        dc.getcontext().rounding = dc.ROUND_HALF_UP
        base, vat, total, unit = self.component.get_amounts_between_dates(
            dt.date(2021, 2, 20),
            dt.date(2021, 3, 13)
        )
        print(base)
        print(vat)
        print(total)
        print(unit)
