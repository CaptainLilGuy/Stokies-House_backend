# from decimal import Decimal
from django.test import TestCase, SimpleTestCase
# from datetime import timedelta
# from django.utils import timezone
# from rest_framework.test import APIClient
# from users.models import User
# from households.models import Household, HouseholdMember
# from .models import Item, InventoryTransaction
from .parser import merge_page_items


def it(name, qty, price):
    return {'name': name, 'quantity': qty, 'unit_price': price, 'needs_review': False}

class MergePagesTests(SimpleTestCase):
    def test_two_item_overlap_is_dropped(self):
        a = [it('INDOMIE GORENG', 1, 3500), it('TELUR 1KG', 1, 28000), it('GULA 1KG', 1, 17000)]
        b = [it('TELUR 1KG', 1, 28000), it('GULA 1KG', 1, 17000), it('MINYAK 2L', 1, 38000)]
        out = merge_page_items([a, b])
        self.assertEqual([i['name'] for i in out],
                         ['INDOMIE GORENG', 'TELUR 1KG', 'GULA 1KG', 'MINYAK 2L'])

    def test_ocr_noise_still_matches(self):
        a = [it('TELUR 1KG', 1, 28000), it('GULA 1KG', 1, 17000)]
        b = [it('TELUR 1 KG', 1, 28000), it('GULA 1KG', 1, 17000), it('KOPI', 1, 9000)]
        self.assertEqual(len(merge_page_items([a, b])), 3)

    def test_single_repeat_is_kept_and_flagged(self):
        a = [it('AQUA 600ML', 1, 4000)]
        b = [it('AQUA 600ML', 1, 4000), it('ROTI', 1, 15000)]
        out = merge_page_items([a, b])
        self.assertEqual(len(out), 3)
        self.assertTrue(out[1]['needs_review'])

    def test_no_overlap_concatenates(self):
        a = [it('A', 1, 1000)]
        b = [it('B', 1, 2000)]
        self.assertEqual(len(merge_page_items([a, b])), 2)


# class UnitPriceTests(TestCase):
#     def setUp(self):
#         self.user = User.objects.create_user('budi', password='x')
#         self.hh = Household.objects.create(name='Budi', created_by=self.user)
#         HouseholdMember.objects.create(household=self.hh, user=self.user, role='owner')
#         self.client = APIClient()
#         self.client.force_authenticate(self.user)

#     def _item(self, **kw):
#         res = self.client.post('/api/inventory/items/', {'name': 'Telur', 'unit': 'kg', 'quantity': 1, **kw}, format='json')
#         return res

#     def test_create_item_stores_price_on_initial_purchase(self):
#         res = self._item(unit_price=28100, source='ocr')
#         self.assertEqual(res.status_code, 201)
#         t = InventoryTransaction.objects.get()
#         self.assertEqual(t.unit_price, Decimal('28100.00'))
#         self.assertEqual(t.source, 'ocr')

#     def test_negative_price_rejected_and_nothing_saved(self):
#         res = self._item(unit_price=-5)
#         self.assertEqual(res.status_code, 400)
#         self.assertEqual(Item.objects.count(), 0)

#     def test_restock_with_price_updates_last_unit_price(self):
#         item_id = self._item(unit_price=28100).data['id']
#         self.client.post('/api/inventory/transactions/', {
#             'item': item_id, 'change_type': 'restocked',
#             'quantity_delta': '2.00', 'unit_price': '31500'}, format='json')
#         res = self.client.get('/api/inventory/items/')
#         self.assertEqual(Decimal(res.data[0]['last_unit_price']), Decimal('31500.00'))

#     def test_price_rejected_on_consumption(self):
#         item_id = self._item().data['id']
#         res = self.client.post('/api/inventory/transactions/', {
#             'item': item_id, 'change_type': 'consumed',
#             'quantity_delta': '-0.50', 'unit_price': '1000'}, format='json')
#         self.assertEqual(res.status_code, 400)

#     def test_cannot_log_transaction_on_other_household_item(self):
#         other = User.objects.create_user('siti', password='x')
#         hh2 = Household.objects.create(name='Siti', created_by=other)
#         HouseholdMember.objects.create(household=hh2, user=other, role='owner')
#         foreign = Item.objects.create(name='X', household=hh2)
#         res = self.client.post('/api/inventory/transactions/', {
#             'item': foreign.id, 'change_type': 'restocked', 'quantity_delta': '1.00'}, format='json')
#         self.assertEqual(res.status_code, 400)
# from datetime import timedelta
# from decimal import Decimal
# from django.test import TestCase
# from django.utils import timezone
# from rest_framework.test import APIClient
# from users.models import User
# from households.models import Household, HouseholdMember
# from .models import Item, InventoryTransaction


# class DashboardTests(TestCase):
#     def setUp(self):
#         self.user = User.objects.create_user('budi', password='x')
#         self.hh = Household.objects.create(name='Budi', created_by=self.user)
#         HouseholdMember.objects.create(household=self.hh, user=self.user, role='owner')
#         self.client = APIClient()
#         self.client.force_authenticate(self.user)
#         self.item = Item.objects.create(name='Telur', unit='kg', household=self.hh)

#     def tx(self, change, delta, price=None, **ago):
#         t = InventoryTransaction.objects.create(
#             item=self.item, household=self.hh, user=self.user,
#             change_type=change, quantity_delta=Decimal(delta), unit_price=price)
#         # created_at is auto_now_add, so backdate with update()
#         InventoryTransaction.objects.filter(pk=t.pk).update(
#             created_at=timezone.now() - timedelta(**ago))

#     def get(self):
#         res = self.client.get('/api/dashboard/')
#         self.assertEqual(res.status_code, 200)
#         return res.data

#     # ── card 3 ──
#     def test_price_increase_is_flagged_against_previous_three_average(self):
#         for p, d in ((28000, 12), (28200, 8), (28100, 4)):
#             self.tx('purchased', '1', price=Decimal(p), days=d)
#         self.tx('restocked', '1', price=Decimal(31500), days=1)
#         pc = self.get()['price_changes']
#         self.assertEqual(len(pc), 1)
#         self.assertEqual(pc[0]['baseline_price'], 28100.0)
#         self.assertEqual(pc[0]['change_pct'], 12.1)
#         self.assertEqual(pc[0]['baseline_count'], 3)

#     def test_small_change_is_ignored(self):
#         self.tx('purchased', '1', price=Decimal(28000), days=5)
#         self.tx('restocked', '1', price=Decimal(29000), days=1)
#         self.assertEqual(self.get()['price_changes'], [])

#     def test_single_priced_purchase_has_no_baseline(self):
#         self.tx('purchased', '1', price=Decimal(28000), days=1)
#         self.assertEqual(self.get()['price_changes'], [])

#     def test_stale_latest_purchase_is_ignored(self):
#         self.tx('purchased', '1', price=Decimal(20000), days=60)
#         self.tx('restocked', '1', price=Decimal(30000), days=45)
#         self.assertEqual(self.get()['price_changes'], [])

#     # ── card 5 (minute offsets keep events inside "this month") ──
#     def test_waste_is_valued_at_price_as_of_the_event(self):
#         self.tx('purchased', '5', price=Decimal(10000), minutes=30)
#         self.tx('wasted', '-2', minutes=20)
#         self.tx('restocked', '5', price=Decimal(20000), minutes=10)  # later price must not count
#         w = self.get()['waste']['this_month']
#         self.assertEqual(w['value'], 20000.0)
#         self.assertEqual(w['events'], 1)
#         self.assertEqual(w['unvalued_events'], 0)

#     def test_waste_without_any_price_is_counted_but_unvalued(self):
#         self.tx('purchased', '5', minutes=30)          # no price recorded
#         self.tx('wasted', '-1', minutes=20)
#         w = self.get()['waste']['this_month']
#         self.assertEqual((w['value'], w['events'], w['unvalued_events']), (0.0, 1, 1))

#     def test_no_household_returns_empty_payload(self):
#         loner = User.objects.create_user('loner', password='x')
#         c = APIClient(); c.force_authenticate(loner)
#         res = c.get('/api/dashboard/')
#         self.assertFalse(res.data['has_household'])
#         self.assertEqual(res.data['price_changes'], [])