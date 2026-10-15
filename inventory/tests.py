from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from users.models import User
from households.models import Household, HouseholdMember
from .models import Item, InventoryTransaction


class UnitPriceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('budi', password='x')
        self.hh = Household.objects.create(name='Budi', created_by=self.user)
        HouseholdMember.objects.create(household=self.hh, user=self.user, role='owner')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def _item(self, **kw):
        res = self.client.post('/api/inventory/items/', {'name': 'Telur', 'unit': 'kg', 'quantity': 1, **kw}, format='json')
        return res

    def test_create_item_stores_price_on_initial_purchase(self):
        res = self._item(unit_price=28100, source='ocr')
        self.assertEqual(res.status_code, 201)
        t = InventoryTransaction.objects.get()
        self.assertEqual(t.unit_price, Decimal('28100.00'))
        self.assertEqual(t.source, 'ocr')

    def test_negative_price_rejected_and_nothing_saved(self):
        res = self._item(unit_price=-5)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(Item.objects.count(), 0)

    def test_restock_with_price_updates_last_unit_price(self):
        item_id = self._item(unit_price=28100).data['id']
        self.client.post('/api/inventory/transactions/', {
            'item': item_id, 'change_type': 'restocked',
            'quantity_delta': '2.00', 'unit_price': '31500'}, format='json')
        res = self.client.get('/api/inventory/items/')
        self.assertEqual(Decimal(res.data[0]['last_unit_price']), Decimal('31500.00'))

    def test_price_rejected_on_consumption(self):
        item_id = self._item().data['id']
        res = self.client.post('/api/inventory/transactions/', {
            'item': item_id, 'change_type': 'consumed',
            'quantity_delta': '-0.50', 'unit_price': '1000'}, format='json')
        self.assertEqual(res.status_code, 400)

    def test_cannot_log_transaction_on_other_household_item(self):
        other = User.objects.create_user('siti', password='x')
        hh2 = Household.objects.create(name='Siti', created_by=other)
        HouseholdMember.objects.create(household=hh2, user=other, role='owner')
        foreign = Item.objects.create(name='X', household=hh2)
        res = self.client.post('/api/inventory/transactions/', {
            'item': foreign.id, 'change_type': 'restocked', 'quantity_delta': '1.00'}, format='json')
        self.assertEqual(res.status_code, 400)