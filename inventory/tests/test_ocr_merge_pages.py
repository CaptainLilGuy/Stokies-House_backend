from ..parser import merge_page_items
from django.test import TestCase, SimpleTestCase

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