"""
Indomaret receipt parser (geometry based).

Input is ML Kit output WITH line geometry, one dict per photo:
    {'lines': [{'text': str, 'box': [l, t, r, b], 'corners': [[x, y] * 4]}, ...]}

Why geometry: ML Kit splits the name / qty+price / line-total columns into
separate chunks, so the text alone cannot say which price belongs to which item.
Here the lines are de-skewed, grouped into physical rows by vertical position,
and every row is read as   NAME  QTY  UNIT_PRICE  LINE_TOTAL.

Two receipt eras are handled:
  2018-style : vouchers/discounts are listed in the footer, after HARGA JUAL
  2026-style : "VOUCHER : (700)" sits right under the item it applies to,
               footer is TOTAL BELANJA / NON TUNAI / ANDA HEMAT / PPN / HARGA JUAL
               (there HARGA JUAL is the taxable base, NOT the sum of the items)
"""
import math
import re
from statistics import median

INDOMARET_THRESHOLD = 4
MIN_UNIT_PRICE = 100      # "PLASTIK SDG 1 1 1" is not a product
MIN_DISCOUNT = 100        # "DISKON : (1)" is a marker, not money

# ── detection ───────────────────────────────────────────────────────────
# The header is unreliable (OCR turned INDOMARCO into FIRRURPRISMAAW and the
# logo into "Sndmae"), so score on lines that survived OCR in every sample.
_DT = re.compile(r'(?<!\d)(\d{2})\.(\d{2})\.(\d{2})-(\d{2}):(\d{2})')
_SIGNALS = [
    (_DT, 3),                                                      # 16.06.18-17:08
    (re.compile(r'\b\d{5,6}/[A-Z ]{3,}/\d{2}\b'), 2),              # 301135/RATIH/01
    (re.compile(r'\b[A-Z0-9]{3,5}-\d{4,6}/[A-Z ]{3,}/\d{2}\b'), 2),  # T1NY-36372/MUHAM/02
    (re.compile(r'HARGA\s+JUAL'), 2),
    (re.compile(r'ANDA\s+HEMAT'), 2),
    (re.compile(r'TOTAL\s+BELANJA'), 2),
    (re.compile(r'PPN\s*:?\s*DPP'), 2),
    (re.compile(r'NON\s+TUNAI'), 1),
    (re.compile(r'INDOMARET|INDOMARCO'), 2),
    (re.compile(r'\bVOUCHER\b'), 1),
    (re.compile(r'\bKEMBALI\b'), 1),
]


def indomaret_score(raw_texts):
    text = '\n'.join(raw_texts).upper()
    return sum(w for rx, w in _SIGNALS if rx.search(text))


# ── amounts ─────────────────────────────────────────────────────────────
_AMOUNT = re.compile(r'\d{1,3}(?:[.,]\d{3})+|\d+')
_PAREN_AMT = re.compile(r'\(\s*(\d{1,3}(?:[.,]\d{3})+|\d+)\s*\)\s*$')
_CANCEL = re.compile(r'\(\s*(\d{1,3})\s*\)\s*\(\s*(\d+)\s*\)\s*\(\s*(\d{1,3}(?:[.,]\d{3})*|\d+)\s*\)')


def _to_int(s):
    s = s.strip().strip('()').strip()
    if re.fullmatch(r'\d{1,3}(?:[.,]\d{3})+', s):
        return int(re.sub(r'[.,]', '', s))
    return int(s) if s.isdigit() else None


def _last_amount(text):
    found = _AMOUNT.findall(text)
    return _to_int(found[-1]) if found else None


# ── geometry ────────────────────────────────────────────────────────────
def _prep(lines):
    out = []
    for ln in lines or []:
        text = (ln.get('text') or '').strip()
        if not re.search(r'[A-Za-z0-9]', text):      # drop "-------" dividers
            continue
        pts = ln.get('corners') or []
        if len(pts) == 4:
            cx = sum(p[0] for p in pts) / 4.0
            cy = sum(p[1] for p in pts) / 4.0
            h = math.hypot(pts[3][0] - pts[0][0], pts[3][1] - pts[0][1])
        elif ln.get('box'):
            l, t, r, b = ln['box']
            cx, cy, h = (l + r) / 2.0, (t + b) / 2.0, float(b - t)
        else:
            continue
        out.append({'text': text, 'cx': cx, 'cy': cy, 'h': max(h, 1.0)})
    return out


def _rotate(items, theta):
    s, c = math.sin(theta), math.cos(theta)
    for it in items:
        it['x'] = it['cx'] * c + it['cy'] * s
        it['y'] = -it['cx'] * s + it['cy'] * c


def _cluster(items, tol):
    rows = []
    for it in sorted(items, key=lambda i: i['y']):
        if rows and abs(it['y'] - rows[-1]['y']) <= tol:
            r = rows[-1]
            r['items'].append(it)
            r['y'] = sum(i['y'] for i in r['items']) / len(r['items'])
        else:
            rows.append({'y': it['y'], 'items': [it]})
    return rows


def _best_angle(items):
    """A photo is rarely level: across the receipt width the right-hand columns
    drift ~half a row lower. Try tilts and keep the one giving the fewest rows
    (columns line up), then the tightest rows, then the smallest tilt."""
    if len(items) < 3:
        return 0.0
    tol = 0.45 * median(i['h'] for i in items)
    best = None
    for k in range(-30, 31):
        th = k * 0.004
        _rotate(items, th)
        rows = _cluster(items, tol)
        spread = sum((i['y'] - r['y']) ** 2 for r in rows for i in r['items'])
        key = (len(rows), round(spread, 1), abs(th))
        if best is None or key < best[0]:
            best = (key, th)
    return best[1]


def _rows_of(items):
    _rotate(items, _best_angle(items))
    tol = 0.45 * median(i['h'] for i in items)
    return [' '.join(i['text'] for i in sorted(r['items'], key=lambda i: i['x']))
            for r in _cluster(items, tol)]


# ── row interpretation ──────────────────────────────────────────────────
_FOOTER = [
    ('total', re.compile(r'^TOTAL(?:\s+BELANJA)?\b')),
    ('harga_jual', re.compile(r'^HARGA\s+JUAL\b')),
    ('ppn', re.compile(r'^PPN\b')),
    ('paid', re.compile(r'^(?:NON\s+)?TUNAI\b')),
    ('change', re.compile(r'^KEMBALI\b')),
    ('savings', re.compile(r'^ANDA\s+HEMAT\b')),
]
_FOOTER_START = {'total', 'harga_jual', 'ppn'}


def _footer_key(text):
    up = text.upper().strip(' -:')
    for key, rx in _FOOTER:
        if rx.search(up):
            return key
    return None


def _item_row(text):
    t = text.split()
    if len(t) < 4 or any(x.startswith('(') for x in t[-3:]):
        return None
    total, price = _to_int(t[-1]), _to_int(t[-2])
    if total is None or price is None or not re.fullmatch(r'\d{1,3}', t[-3]):
        return None
    name = ' '.join(t[:-3]).strip(' :')
    if not re.search(r'[A-Za-z]{2}', name):
        return None
    return name, int(t[-3]), price, total


def _apply_cancel(items, qty, price):
    for i in range(len(items) - 1, -1, -1):
        it = items[i]
        if it['unit_price'] == price and it['quantity'] >= qty:
            if it['quantity'] == qty:
                items.pop(i)
            else:
                it['quantity'] -= qty
                it['needs_review'] = True
                it['issues'].append('partially_cancelled')
            return True
    return False


def parse_page(lines):
    items = _prep(lines)
    date = None
    anchor = next((i for i in sorted(items, key=lambda i: i['cy']) if _DT.search(i['text'])), None)
    if anchor:
        m = _DT.search(anchor['text'])
        date = f'{m.group(1)}.{m.group(2)}.{m.group(3)}'
        # everything above the date/time row is header or background clutter
        items = [i for i in items if i['cy'] >= anchor['cy'] - anchor['h']]

    out = {'items': [], 'footer': {}, 'ppn_seen': False,
           'footer_discount': 0, 'date': date, 'warnings': []}
    if not items:
        return out

    in_footer = False
    for row in _rows_of(items):
        key = _footer_key(row)
        if not in_footer and key in _FOOTER_START:
            in_footer = True

        if in_footer:
            if key == 'ppn':
                out['ppn_seen'] = True
            elif key:
                out['footer'].setdefault(key, _last_amount(row))
            else:
                m = _PAREN_AMT.search(row)           # 2018: VOUCHER ... : (3,600)
                if m and _to_int(m.group(1)) >= MIN_DISCOUNT:
                    out['footer_discount'] += _to_int(m.group(1))
            continue

        cm = _CANCEL.search(row)
        if cm:
            if not _apply_cancel(out['items'], int(cm.group(1)), _to_int(cm.group(2))):
                out['warnings'].append(f'cancel row without matching item: {row}')
            continue

        parsed = _item_row(row)
        if parsed:
            name, qty, price, total = parsed
            if price < MIN_UNIT_PRICE:
                continue
            ok = qty * price == total
            out['items'].append({
                'name': name, 'quantity': qty, 'unit_price': price, 'discount': 0,
                'needs_review': not ok,
                'issues': [] if ok else [f'qty*price != printed total ({total})'],
            })
            continue

        m = _PAREN_AMT.search(row)                   # 2026: VOUCHER : (700) under an item
        if m and out['items'] and _to_int(m.group(1)) >= MIN_DISCOUNT:
            out['items'][-1]['discount'] += _to_int(m.group(1))
    return out


def parse_indomaret(ocr_pages):
    """-> {'items', 'total', 'date', 'meta'} for one or more photos, in order."""
    from .parser import merge_page_items          # lazy: parser.py imports this module

    pages = [parse_page(p.get('lines', [])) for p in ocr_pages]
    items = merge_page_items([p['items'] for p in pages])

    footer = {}
    for p in pages:                               # later pages win (footer is last)
        footer.update({k: v for k, v in p['footer'].items() if v is not None})
    ppn_seen = any(p['ppn_seen'] for p in pages)
    date = next((p['date'] for p in pages if p['date']), None)

    gross = sum(i['quantity'] * i['unit_price'] for i in items)
    discount = sum(i['discount'] for i in items) + sum(p['footer_discount'] for p in pages)
    net = gross - discount

    checks = {}
    if footer.get('total') is not None:
        checks['net_matches_total'] = net == footer['total']
    if footer.get('harga_jual') is not None and not ppn_seen:
        checks['gross_matches_harga_jual'] = gross == footer['harga_jual']
    if footer.get('savings') is not None:
        checks['discounts_match_savings'] = discount == footer['savings']

    return {
        'items': items,
        'total': footer.get('total'),
        'date': date,
        'meta': {'vendor': 'indomaret', 'items_sum': gross, 'discount_total': discount,
                 'net': net, 'footer': footer, 'checks': checks,
                 'warnings': [w for p in pages for w in p['warnings']]},
    }