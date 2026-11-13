from decimal import Decimal

from django.db.models import F
from django.test import TestCase
from django.utils import timezone

from households.models import HouseholdMember
from users.models import User
from ..models import InventoryTransaction, Item, Household

class TipsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('budi', password='x')
        self.hh = Household.objects.create(name='Budi', created_by=self.user)
        HouseholdMember.objects.create(household=self.hh, user=self.user, role='owner')
        self.item = Item.objects.create(name='Telur', unit='pcs', household=self.hh)

    def tx(self, change, delta):
        InventoryTransaction.objects.create(item=self.item, household=self.hh, user=self.user,
                                            change_type=change, quantity_delta=Decimal(delta))
        Item.objects.filter(pk=self.item.pk).update(quantity=F('quantity') + Decimal(delta))
        self.item.refresh_from_db()

    def run_low(self):
        from ..dashboard import stock_ledger, low_stock
        return low_stock([self.item], stock_ledger(self.hh), timezone.now())

    def test_quarter_of_last_stock_is_low(self):
        self.tx('purchased', '4'); self.tx('consumed', '-3')
        self.assertEqual(self.run_low()[0]['status'], 'low')

    def test_half_left_is_fine(self):
        self.tx('purchased', '4'); self.tx('consumed', '-2')
        self.assertEqual(self.run_low(), [])

    def test_zero_is_out(self):
        self.tx('purchased', '2'); self.tx('consumed', '-2')
        self.assertEqual(self.run_low()[0]['status'], 'out')