import re

KEYWORD_LINES = {
    'diskon', 'harga jual', 'total', 'tunai', 'kembali', 'anda hemat',
    'terima kasih', 'layanan konsumen', 'promosi',
}

KEYWORD_ALIASES = {
    'harga': 'harga jual',
    'jual': 'harga jual',
}

PRICE_TOKEN = r'\d{1,3}([.,]\s?\d{3})+|\d{3,}'
PRICE_PATTERN = re.compile(rf'^\(?({PRICE_TOKEN})\)?$')
FOOTER_VALUE_PATTERN = re.compile(rf'^:?\s*\(?({PRICE_TOKEN}|\d{{1,3}})\)?$')  # accepts (1), :(1,300), (500)
QTY_PATTERN = re.compile(r'^\d{1,2}$')
QTY_PRICE_COMBINED_PATTERN = re.compile(rf'^(\d{{1,2}})\s+({PRICE_TOKEN})$')  # e.g. "1 13500"
DATE_PATTERN = re.compile(r'\d{1,2}[.\-/]\s?\d{1,2}[.\-/]\s?\d{2,4}')
HEADER_NOISE_PATTERN = re.compile(
    r'(\d{1,2}[.\-/]\s?\d{1,2}[.\-/]\s?\d{2,4})|'
    r'(\d{1,2}:\d{2})|'
    r'([A-Za-z0-9]{6,}\d{3,})|'
    r'(km\.|kab\.|sumeda)',
    re.IGNORECASE
)
FOOTER_KEYWORDS_ORDER = ['diskon', 'harga jual', 'total', 'tunai', 'kembali', 'anda hemat']

def match_keyword(lower_line: str):
    """Returns the canonical keyword this line matches, or None."""
    for kw in FOOTER_KEYWORDS_ORDER:
        if kw in lower_line:
            return kw
    for alias, canonical in KEYWORD_ALIASES.items():
        if alias in lower_line:
            return canonical
    return None

def is_header_noise(line: str) -> bool:
    stripped = line.strip()
    if HEADER_NOISE_PATTERN.search(stripped):
        return True
    if ' ' not in stripped and len(stripped) < 15 and not any(c.isdigit() for c in stripped):
        return True
    return False


def strip_header_noise(lines):
    first_data_idx = None
    for i, line in enumerate(lines):
        if QTY_PATTERN.match(line.strip()) or PRICE_PATTERN.match(line.strip()):
            first_data_idx = i
            break
    if first_data_idx is None:
        return lines
    header = [l for l in lines[:first_data_idx] if not is_header_noise(l)]
    rest = lines[first_data_idx:]
    return header + rest


# ── layout detection ──────────────────────────────────────

def detect_layout(lines):
    combined_hits = sum(1 for l in lines if QTY_PRICE_COMBINED_PATTERN.match(l.strip()))
    separated_hits = sum(1 for l in lines if QTY_PATTERN.match(l.strip()))
    if combined_hits == 0 and separated_hits == 0:
        return 'unknown'
    return 'combined' if combined_hits >= separated_hits else 'separated'


# ── 'separated' layout (name / qty / price each their own line-block) ──

def classify_line(line: str) -> str:
    stripped = line.strip()
    lower = stripped.lower()
    if match_keyword(lower):
        return 'keyword'
    if PRICE_PATTERN.match(stripped):
        return 'price'
    if QTY_PATTERN.match(stripped):
        return 'qty'
    if len(stripped) >= 4 and not stripped.replace(' ', '').isdigit():
        return 'item_name'
    return 'unknown'


def group_consecutive(lines_with_types):
    groups = []
    current_type = None
    current_group = []
    for line, ltype in lines_with_types:
        if ltype != current_type:
            if current_group:
                groups.append((current_type, current_group))
            current_type = ltype
            current_group = [line]
        else:
            current_group.append(line)
    if current_group:
        groups.append((current_type, current_group))
    return groups


def extract_items(groups):
    items = []
    i = 0
    while i < len(groups):
        gtype, glines = groups[i]

        if gtype == 'keyword':
            break  # footer reached — stop, everything after is not an item

        if gtype == 'item_name':
            names = glines
            qtys, prices = [], []
            j = i + 1
            while j < len(groups) and groups[j][0] not in ('item_name', 'keyword'):
                if groups[j][0] == 'qty' and not qtys:
                    qtys = groups[j][1]
                elif groups[j][0] == 'price' and not prices:
                    prices = groups[j][1]
                j += 1
            counts_match = len(names) == len(qtys) == len(prices)
            for idx, name in enumerate(names):
                qty = qtys[idx] if idx < len(qtys) else None
                price = prices[idx] if idx < len(prices) else None
                items.append({
                    'name': name.strip(),
                    'quantity': int(qty) if qty else None,
                    'unit_price': _parse_price(price) if price else None,
                    'needs_review': not counts_match,
                })
            i = j
        else:
            i += 1
    return items


def parse_separated_layout(lines):
    lines_with_types = [(line, classify_line(line)) for line in lines]
    groups = group_consecutive(lines_with_types)
    return extract_items(groups)


# ── 'combined' layout (qty+price on one line, e.g. "1 13500") ──

def parse_combined_layout(lines):
    names = []
    qty_prices = []
    for line in lines:
        stripped = line.strip()
        match = QTY_PRICE_COMBINED_PATTERN.match(stripped)
        if match:
            qty_prices.append((match.group(1), match.group(2)))
            continue

        lower = stripped.lower()
        if any(kw in lower for kw in KEYWORD_LINES):
            continue  # footer line, not an item
        if PRICE_PATTERN.match(stripped):
            continue  # FIX: bare line-total (e.g. "20,000") — not an item name
        if '=' in stripped:
            continue  # FIX: tax/meta breakdown lines (e.g. "PN : DPP- 16,517 PN= 1,982")

        if len(stripped) >= 4 and not stripped.replace(' ', '').isdigit():
            names.append(stripped)

    counts_match = len(names) == len(qty_prices)
    items = []
    for idx, name in enumerate(names):
        if idx < len(qty_prices):
            qty, price = qty_prices[idx]
            items.append({
                'name': name, 'quantity': int(qty), 'unit_price': _parse_price(price),
                'needs_review': not counts_match,
            })
        else:
            items.append({'name': name, 'quantity': None, 'unit_price': None, 'needs_review': True})
    return items


def parse_items(lines):
    """Entry point: detects layout and branches. Returns (items, layout_used)."""
    layout = detect_layout(lines)
    if layout == 'combined':
        return parse_combined_layout(lines), layout
    elif layout == 'separated':
        return parse_separated_layout(lines), layout
    else:
        return [], 'unrecognized'


# ── shared helpers ──────────────────────────────────────

def _parse_price(raw: str):
    cleaned = raw.strip().strip('()').replace(' ', '')
    cleaned = re.sub(r'[.,](?=\d{3})', '', cleaned)
    try:
        return int(cleaned)
    except ValueError:
        return None


def extract_footer_values(lines):
    result = {}
    pending_keywords = []
    value_lines = []

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()
        matched_kw = next((kw for kw in FOOTER_KEYWORDS_ORDER if kw in lower), None)

        if matched_kw:
            inline_match = re.search(PRICE_TOKEN, stripped)  # FIX: check same line first
            if inline_match:
                key = matched_kw if matched_kw not in result else f"{matched_kw}_{len(result)}"
                result[key] = _parse_price(inline_match.group())
            else:
                pending_keywords.append(matched_kw)
            continue

        if pending_keywords and FOOTER_VALUE_PATTERN.match(stripped):
            value_lines.append(stripped)

    # original block-alignment fallback, unchanged — for keywords with no inline value
    n = len(pending_keywords)
    relevant_values = value_lines[-n:] if n else []
    for idx, kw in enumerate(pending_keywords):
        if idx < len(relevant_values):
            key = kw if kw not in result else f"{kw}_{len(result)}"
            result[key] = _parse_price(relevant_values[idx])

    return result


def extract_total(lines):
    return extract_footer_values(lines).get('total')


def extract_date(lines):
    for line in lines:
        match = DATE_PATTERN.search(line)
        if match:
            return match.group()
    return None