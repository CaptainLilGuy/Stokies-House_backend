"""
Run from the Django project root:   python -m unittest inventory.test_indomaret_parser -v

FIXTURE_2018, FIXTURE_2026_A and FIXTURE_2026_B are real ML Kit output (text + corner points).
FIXTURE_2026 and FIXTURE_CROP are synthetic: clean upright geometry laid out like the photos.
"""
import unittest
from ..indomaret_parser import indomaret_score, parse_indomaret, parse_page


def P(text, x0, y0, x1, y1, x2, y2, x3, y3):
    return {'text': text, 'corners': [[x0, y0], [x1, y1], [x2, y2], [x3, y3]]}


FIXTURE_2018 = [
    P('FIRRURPRISMAAW', 35, 4, 193, 16, 192, 27, 34, 15),
    P('NPNP O1.337 904 8-062 000', 37, 43, 176, 53, 175, 64, 36, 54),
    P('BESI JANGKANG KM. 1.5/004 02744464894', 50, 101, 332, 118, 330, 136, 48, 119),
    P('SUKOHARJO, NGAGLIK, SLEMAN, SLEMAN, 5558', 41, 143, 346, 158, 345, 175, 40, 160),
    P('16.06.18-17:08', 24, 182, 134, 186, 133, 202, 23, 198),
    P('2.1.27', 167, 188, 209, 189, 208, 206, 166, 205),
    P('ABC ORANGE 525ML', 22, 221, 149, 224, 148, 240, 21, 237),
    P('I/F BISC.WNDRLND 300', 22, 240, 177, 243, 176, 260, 21, 257),
    P('LEXUS SANDW COKL 190', 22, 260, 176, 262, 175, 277, 21, 275),
    P('LUWAK WHT ORGL 20X20', 22, 279, 175, 280, 174, 295, 21, 294),
    P('ORED CH0 & VAN 2X137', 21, 297, 172, 299, 171, 314, 20, 312),
    P('TONG TJI JASM T/A.25', 21, 315, 173, 316, 172, 333, 20, 332),
    P('KOPIKO 78C 240ML', 21, 332, 141, 334, 140, 350, 20, 348),
    P('FRSTEA TEH MADU 350', 22, 351, 164, 353, 163, 367, 21, 365),
    P('SOVIA M/GORENG 2L', 21, 368, 147, 369, 146, 384, 20, 383),
    P('Sndmae', 244, 34, 350, 43, 347, 66, 241, 57),
    P('CANCEL:', 112, 386, 169, 388, 168, 407, 111, 405),
    P('301135/RATIH/01', 232, 191, 343, 196, 342, 213, 231, 208),
    P('1 13500', 216, 226, 267, 228, 266, 245, 215, 243),
    P('1 20900', 209, 245, 266, 247, 265, 262, 208, 260),
    P('1 26800', 214, 262, 265, 264, 264, 281, 213, 279),
    P('1 25400', 213, 281, 264, 283, 263, 300, 212, 298),
    P('1 19800', 207, 300, 262, 303, 261, 317, 206, 314),
    P('1 9300', 212, 317, 262, 318, 261, 336, 211, 335),
    P('2 5500', 203, 337, 260, 339, 259, 353, 202, 351),
    P('13,500', 300, 232, 344, 234, 343, 250, 299, 248),
    P('20,900', 298, 250, 343, 251, 342, 268, 297, 267),
    P('26,800', 296, 269, 340, 270, 339, 285, 295, 284),
    P('25,400', 296, 287, 340, 289, 339, 305, 295, 303),
    P('19,800', 296, 306, 339, 306, 338, 323, 295, 323),
    P('9,300', 301, 326, 337, 326, 336, 341, 300, 341),
    P('11,000', 294, 342, 336, 343, 335, 359, 293, 358),
    P('1 3950', 204, 355, 259, 357, 258, 372, 203, 370),
    P('1 26950', 210, 373, 259, 374, 258, 390, 209, 389),
    P('(1)(26950) (26,950)', 201, 390, 330, 395, 329, 414, 200, 409),
    P('3,950', 299, 360, 334, 361, 333, 376, 298, 375),
    P('26,950', 290, 377, 334, 380, 332, 395, 288, 392),
    P('HARGA JUAL : 130,650', 169, 426, 328, 431, 327, 447, 168, 442),
    P('VOUCHER ABC SQUASH ORANGE : (3,600)', 57, 439, 327, 450, 326, 467, 56, 456),
    P('VOUCHER INDOFOOD WONDERLAND: (10,000)', 39, 456, 328, 467, 327, 485, 38, 474),
    P('VOUCHER TONG TJI TEA INDONESIA :', 16, 474, 253, 484, 252, 503, 15, 493),
    P('(500)', 296, 489, 330, 489, 330, 501, 296, 501),
]


def R(text, x, y, w=60, h=16):
    return P(text, x, y, x + w, y, x + w, y + h, x, y + h)


FIXTURE_2026 = [  # 04.11.26 receipt: per-item voucher, TOTAL BELANJA / NON TUNAI / PPN
    R('ASUS Vivobook S 14 OLED', 10, 20, 300), R('45 Watts and', 10, 60, 120),
    R('04.11.26-09:40/4.5.3/T1NY-36372/MUHAM/02', 20, 200, 330),
    R('I/OCHA GRN TEA 350ML', 10, 260, 170), R('1 3600', 215, 260, 55), R('3,600', 300, 260, 50),
    R('VOUCHER :', 190, 288, 70), R('(700)', 300, 288, 50),
    R('P/BRD DUO MNTG&COCHP', 10, 316, 170), R('1 4500', 215, 316, 55), R('4,500', 300, 316, 50),
    R('IDM TRUL PACK 50\'S', 10, 344, 160), R('1 4900', 215, 344, 55), R('4,900', 300, 344, 50),
    R('TOTAL BELANJA :', 160, 388, 130), R('12,300', 300, 388, 50),
    R('NON TUNAI :', 180, 430, 100), R('12,300', 300, 430, 50),
    R('ANDA HEMAT :', 170, 458, 110), R('700', 310, 458, 40),
    R('PPN : DPP= 10,736 PPN= 1,288', 10, 486, 260),
    R('HARGA JUAL : 11,712', 10, 514, 200),
    R('NO:************AAAG,PURCHASE:12,300', 10, 542, 330),
]

FIXTURE_CROP = [  # footer-only crop, no header
    R('S/ROTI KRIM KEJU 72G', 5, 10, 150), R('4', 190, 10, 10), R('4500', 230, 10, 40), R('18,000', 290, 10, 50),
    R('CIMORY MIX BERRY 225', 5, 36, 150), R('1', 190, 36, 10), R('8500', 230, 36, 40), R('8,500', 290, 36, 50),
    R('CAFELA EXPRESO 200ML', 5, 62, 150), R('1', 190, 62, 10), R('3500', 230, 62, 40), R('3,500', 290, 62, 50),
    R('FF LOW FAT VAN 225', 5, 88, 150), R('1', 190, 88, 10), R('5200', 230, 88, 40), R('5,200', 290, 88, 50),
    R('PLASTIK SDG', 5, 114, 100), R('1', 190, 114, 10), R('1', 240, 114, 10), R('1', 320, 114, 10),
    R('DISKON : ( 1)', 200, 140, 140),
    R('HARGA JUAL : 35,200', 150, 180, 190),
    R('DISKON FRISIAN FLAG : (1,300)', 60, 206, 280),
    R('TOTAL : 33,900', 190, 250, 150), R('TUNAI : 40,000', 190, 276, 150),
    R('KEMBALI : 6,100', 190, 302, 150), R('ANDA HEMAT : 1,300', 170, 328, 170),
]


Q = P


# 05.11.26 receipt: real ML Kit output (photo is level; footer lines of the paper curl slightly)
FIXTURE_2026_A = [
    Q('PT INDOMARCO PRISMATAMA', 167,346,425,346,425,362,167,362),
    Q('GEDUNG MENARA', 167,365,322,365,322,382,167,382),
    Q('INDOMARET BOULEVARD', 167,385,386,385,386,402,167,402),
    Q('PANTAI INDAH KAPUK', 166,403,349,403,349,419,166,419),
    Q('JAIARTA UTARA', 167,423,307,423,307,438,167,438),
    Q('NPWP 001337 994 6-092 000', 166,441,407,441,407,462,166,462),
    Q('ANGGREK CAKRA 25', 253,472,439,472,439,493,253,493),
    Q('JALAN ANGGREK CAKRA NO 25 SUKABUMI UTARA', 125,509,591,509,591,535,125,535),
    Q('KEC. KEBON JERUK, KOTA JAKARTA BARAT, 11540', 113,550,615,550,615,575,113,575),
    Q('05.11.26-09:20/4.5.3/T1NY-30345/AMELI/O1', 128,626,587,630,586,654,127,650),
    Q('MAXICORN BBQ 1306', 116,704,308,704,308,727,116,727),
    Q('NESCAFE LATTE 220ML', 116,777,329,780,328,803,115,800),
    Q('1 11400', 402,705,481,705,481,733,402,733),
    Q('VOUCHER :', 379,744,477,745,476,767,378,766),
    Q('1 7900', 392,784,480,784,480,806,392,806),
    Q('TOTAL BELANJA :', 309,856,476,858,475,881,308,879),
    Q('NON TUNAI:', 357,931,480,933,479,959,356,957),
    Q('ANDA HEMAT :', 342,969,474,973,473,995,341,991),
    Q('PPN : DPP= 15,938 PPN= 1,913', 114,998,476,1005,475,1034,113,1027),
    Q('HARGA JUAL : 17,387', 114,1038,326,1042,325,1066,113,1062),
    Q('Sndsmosel', 493,368,627,375,625,405,491,398),
    Q('LAYANAN KONSUMEN', 190,1154,413,1158,412,1177,189,1173),
    Q('SMSWA 0811.1500.280 TELP 1600280', 116,1174,482,1183,481,1206,115,1197),
    Q('KONTAK@INDOMARET.CO. ID', 157,1200,449,1205,448,1227,156,1222),
    Q('BELANJA LEBIH MUDAH DI', 164,1223,441,1230,440,1249,163,1242),
    Q('KLIKINDOMARET', 215,1250,380,1254,379,1271,214,1267),
    Q('11,400', 533,709,600,709,600,731,533,731),
    Q('OR BCA-TRXID:T1NY2611050920390101', 170,1078,543,1088,542,1113,169,1103),
    Q('GRATIS ONGKIR1 JAM SAMPAI', 142,1267,457,1277,456,1299,141,1289),
    Q('(500)', 545,748,596,748,596,771,545,771),
    Q('7,900', 542,786,599,786,599,809,542,809),
    Q('18,800', 530,863,597,863,597,886,530,886),
    Q('NO:**********************AARG,. PURCHASE:18,800', 114,1115,632,1132,631,1156,113,1139),
    Q('18,800', 529,939,595,939,595,963,529,963),
    Q('500', 562,978,595,978,595,1001,562,1001),
]

# 04.11.26 receipt: real ML Kit output; the laptop box above the receipt is read as text too
FIXTURE_2026_B = [
    Q('JS Vivobook S 14 OLED', 0,77,339,91,337,119,-2,105),
    Q('/13 kg', 4,216,49,216,49,231,4,231), Q('chassis', 4,236,46,236,46,251,4,251),
    Q('al lid', 3,255,28,255,28,273,3,273), Q('1', 9,290,31,290,31,341,9,341),
    Q('ED', 0,340,22,340,22,355,0,355), Q('T SELLER', 3,369,52,369,52,379,3,379),
    Q('8889100', 2,389,73,391,72,406,1,404), Q('45 Watts and', 85,218,168,219,167,234,84,233),
    Q('dual fans for better', 84,237,208,242,207,260,83,255),
    Q('performance', 84,258,168,262,167,280,83,276),
    Q('Thickness and weight', 81,359,177,362,176,373,80,370),
    Q('according to specifhcatie', 86,373,184,376,183,386,85,383),
    Q('gnt Vary', 192,369,226,369,226,379,192,379),
    Q('IR camera', 232,223,295,230,293,244,230,237),
    Q('Password-free login backlit keyboard for', 232,244,506,256,505,274,231,262),
    Q('customization', 378,275,470,277,469,291,377,289),
    Q('HDTn ENERGY STAR', 334,382,497,392,495,411,332,401),
    Q('PT INDOMARCO PRISMATAMA', 215,515,399,515,399,531,215,531),
    Q('GEDUNG MENARA', 213,533,325,533,325,544,213,544),
    Q('INDOMARET BOULEVARD', 214,547,368,545,368,557,214,559),
    Q('PANTA INDAH KAPUK', 218,559,345,559,345,573,218,573),
    Q('Single-zone RGB', 380,231,488,235,487,253,379,249),
    Q('JAKAR IA2g0g 6-092 000', 219,571,386,585,384,599,217,585),
    Q('NPWP', 216,588,250,588,250,599,216,599),
    Q('ANGGREK CAKRA 25', 277,603,407,605,406,622,276,620),
    Q('JALAN ANGGREK CAKRA NO 25 SUKABUKI UTARA', 186,632,513,632,513,651,186,651),
    Q('I/0CHA GRN TEA 350ML', 177,774,343,774,343,791,177,791),
    Q('KEC. KEBON JERUK, KOTA JAKARTA BARAT, 11540', 180,663,529,663,529,681,180,681),
    Q('P/BRD DUO MNTG&COCHP', 178,828,340,825,340,841,178,844),
    Q("IDM TRUL PACK 50'S", 181,855,327,855,327,870,181,870),
    Q('04.11.26-09:40/4.5.3/T1NY-36372/MUHAM/02', 185,720,514,720,514,735,185,735),
    Q('1 3600', 378,774,437,774,437,789,378,789),
    Q('PPN', 183,1025,208,1025,208,1042,183,1042),
    Q('HARGA JUAL : 11,712', 182,1054,342,1043,343,1061,183,1072),
    Q('VOUCHER', 369,800,420,800,420,815,369,815),
    Q('ASUS', 453,88,497,88,497,102,453,102), Q('Lumina', 445,102,504,105,503,120,444,117),
    Q('OLED', 451,126,497,126,497,140,451,140),
    Q('1 4500', 383,825,437,825,437,843,383,843), Q('1 4900', 378,854,437,854,437,870,378,870),
    Q('TOTAL BELAN JA', 326,905,423,906,422,922,325,921),
    Q('NON TUNAI', 359,960,422,960,422,976,359,976),
    Q('ANDA HEMAT:', 353,985,439,985,439,1005,353,1005),
    Q(': DPP= 10,736 PPN= 1.288', 260,1019,437,1008,438,1029,261,1040),
    Q('Snooaut)', 446,530,538,528,538,549,446,551),
    Q('LAYANAN KONSUMEN', 249,1135,408,1123,409,1141,250,1153),
    Q('SMSWA 0811.1500.280 TELP 1500280', 188,1159,446,1137,447,1154,189,1176),
    Q('KONTAKaINDOMARET.CO./D', 213,1178,429,1156,430,1172,214,1194),
    Q('BELAN.JA LEBIH MUDAHDI', 223,1194,426,1175,427,1192,224,1211),
    Q('KLIKINDOMARET', 264,1209,391,1199,392,1215,265,1225),
    Q('GRATIS ONGKIR1.JAMSAMPAL', 213,1232,440,1210,441,1226,214,1248),
    Q('3,600', 481,774,522,774,522,790,481,790), Q('(700)', 482,802,518,802,518,818,482,818),
    Q('4,500', 480,830,520,830,520,846,480,846), Q('4,900', 480,857,519,857,519,873,480,873),
    Q('12,300', 474,912,519,912,519,929,474,929),
    Q('OR BCA-TRXID:T 1NY2611040939580102', 227,1078,486,1062,487,1085,228,1101),
    Q('12,300', 474,965,520,965,520,982,474,982),
    Q('NO:X***x****************AAAG,PURCHASE:1', 182,1114,501,1090,502,1109,183,1133),
    Q('700', 497,993,520,993,520,1010,497,1010),
]


def names(res):
    return [(i['name'], i['quantity'], i['unit_price'], i['discount']) for i in res['items']]


class Indomaret(unittest.TestCase):
    def test_2018_real_dump(self):
        r = parse_indomaret([{'lines': FIXTURE_2018}])
        self.assertEqual(names(r), [
            ('ABC ORANGE 525ML', 1, 13500, 0), ('I/F BISC.WNDRLND 300', 1, 20900, 0),
            ('LEXUS SANDW COKL 190', 1, 26800, 0), ('LUWAK WHT ORGL 20X20', 1, 25400, 0),
            ('ORED CH0 & VAN 2X137', 1, 19800, 0), ('TONG TJI JASM T/A.25', 1, 9300, 0),
            ('KOPIKO 78C 240ML', 2, 5500, 0), ('FRSTEA TEH MADU 350', 1, 3950, 0)])  # SOVIA cancelled
        self.assertEqual(r['date'], '16.06.18')
        self.assertIsNone(r['total'])                       # crop ends before TOTAL
        m = r['meta']
        self.assertEqual((m['items_sum'], m['discount_total']), (130650, 14100))
        self.assertTrue(m['checks']['gross_matches_harga_jual'])
        self.assertFalse(any(i['needs_review'] for i in r['items']))

    def test_2026_real_dump_05_11(self):
        r = parse_indomaret([{'lines': FIXTURE_2026_A}])
        self.assertEqual(names(r), [('MAXICORN BBQ 1306', 1, 11400, 500),
                                    ('NESCAFE LATTE 220ML', 1, 7900, 0)])
        self.assertEqual((r['total'], r['date']), (18800, '05.11.26'))
        self.assertTrue(all(r['meta']['checks'].values()))

    def test_2026_real_dump_04_11_with_background_text(self):
        r = parse_indomaret([{'lines': FIXTURE_2026_B}])        # laptop box text must be ignored
        self.assertEqual(names(r), [('I/0CHA GRN TEA 350ML', 1, 3600, 700),
                                    ('P/BRD DUO MNTG&COCHP', 1, 4500, 0),
                                    ("IDM TRUL PACK 50'S", 1, 4900, 0)])
        self.assertEqual((r['total'], r['date']), (12300, '04.11.26'))
        self.assertTrue(all(r['meta']['checks'].values()))

    def test_2026_per_item_voucher(self):
        r = parse_indomaret([{'lines': FIXTURE_2026}])
        self.assertEqual(names(r), [('I/OCHA GRN TEA 350ML', 1, 3600, 700),
                                    ('P/BRD DUO MNTG&COCHP', 1, 4500, 0),
                                    ("IDM TRUL PACK 50'S", 1, 4900, 0)])
        self.assertEqual((r['total'], r['date']), (12300, '04.11.26'))
        c = r['meta']['checks']
        self.assertTrue(c['net_matches_total'] and c['discounts_match_savings'])
        self.assertNotIn('gross_matches_harga_jual', c)     # HARGA JUAL is the taxable base here

    def test_cropped_footer_only(self):
        r = parse_indomaret([{'lines': FIXTURE_CROP}])
        self.assertEqual(len(r['items']), 4)                # PLASTIK and DISKON:(1) ignored
        self.assertEqual(r['total'], 33900)
        self.assertIsNone(r['date'])
        self.assertTrue(all(r['meta']['checks'].values()))

    def test_tilt(self):
        tilted = []
        for ln in FIXTURE_2026:                              # shear: right side drifts down
            pts = [[x, y + 0.05 * x] for x, y in ln['corners']]
            tilted.append({'text': ln['text'], 'corners': pts})
        r = parse_indomaret([{'lines': tilted}])
        self.assertEqual(names(r)[0], ('I/OCHA GRN TEA 350ML', 1, 3600, 700))
        self.assertEqual(len(r['items']), 3)

    def test_misread_digit_is_flagged(self):
        bad = [dict(l) for l in FIXTURE_2026]
        for l in bad:
            if l['text'] == '1 4500':
                l['text'] = '1 4800'
        r = parse_indomaret([{'lines': bad}])
        self.assertTrue(r['items'][1]['needs_review'])
        self.assertFalse(r['meta']['checks']['net_matches_total'])

    def test_detection(self):
        self.assertGreaterEqual(indomaret_score(['\n'.join(l['text'] for l in FIXTURE_2018)]), 4)
        self.assertGreaterEqual(indomaret_score(['\n'.join(l['text'] for l in FIXTURE_CROP)]), 4)
        self.assertLess(indomaret_score(['Toko Maju\nBeras 5kg 1 65000 65.000\nTOTAL 65.000']), 4)


if __name__ == '__main__':
    unittest.main()