"""
GET /api/dashboard/  ->  data for dashboard cards 3 (price changes) and 5 (waste value).

Cards 1, 2 and 4 are still computed client-side from existing endpoints. When you
move them here, add their keys to the payload; the Flutter getters stay the same.
"""
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.db.models import OuterRef, Subquery
from django.utils import timezone
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from households.models import Household
from .models import InventoryTransaction, Item
from households.models import Household, HouseholdMember


CT = InventoryTransaction.ChangeType
STOCK_IN = [CT.PURCHASED, CT.RESTOCKED]

LOW_STOCK_RATIO = Decimal('0.25')
LOW_STOCK_MAX = 5
OUT_OF_STOCK_RECENT_DAYS = 30
USE_FIRST_WINDOW_DAYS = 14
USE_FIRST_MAX = 5


# Tunable DSS assumptions (document these in the thesis, test them in UAT)
PRICE_CHANGE_THRESHOLD_PCT = 10   # ignore moves smaller than this
PRICE_RECENT_DAYS = 30            # only flag items bought within this window
PRICE_BASELINE_N = 3              # compare against the previous N priced purchases
PRICE_MAX_CARDS = 3
WASTE_TOP_ITEMS = 5


def month_starts(now):
    this_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_start = (this_start - timedelta(days=1)).replace(day=1)
    return this_start, last_start


def price_changes(household, now):
    rows = (InventoryTransaction.objects
            .filter(household=household, change_type__in=STOCK_IN,
                    unit_price__isnull=False)
            .order_by('item_id', '-created_at')
            .values('item_id', 'item__name', 'item__unit', 'unit_price', 'created_at'))

    by_item = defaultdict(list)
    for r in rows:
        by_item[r['item_id']].append(r)

    cutoff = now - timedelta(days=PRICE_RECENT_DAYS)
    out = []
    for item_id, txns in by_item.items():
        if len(txns) < 2:
            continue                                   # need a baseline to compare with
        latest, history = txns[0], txns[1:1 + PRICE_BASELINE_N]
        if latest['created_at'] < cutoff:
            continue                                   # stale: not news anymore
        baseline = sum(h['unit_price'] for h in history) / len(history)
        if baseline <= 0:
            continue
        pct = (latest['unit_price'] - baseline) / baseline * 100
        if abs(pct) < PRICE_CHANGE_THRESHOLD_PCT:
            continue
        out.append({
            'item_id': item_id,
            'name': latest['item__name'],
            'unit': latest['item__unit'],
            'last_price': float(latest['unit_price']),
            'last_date': timezone.localtime(latest['created_at']).date().isoformat(),
            'baseline_price': float(round(baseline, 2)),
            'baseline_count': len(history),
            'change_pct': round(float(pct), 1),
        })
    out.sort(key=lambda x: abs(x['change_pct']), reverse=True)
    return out[:PRICE_MAX_CARDS]


def waste_summary(household, now):
    this_start, last_start = month_starts(now)

    # Value each waste event at the latest priced purchase/restock made AT OR BEFORE it
    price_at = Subquery(
        InventoryTransaction.objects
        .filter(item=OuterRef('item'), change_type__in=STOCK_IN,
                unit_price__isnull=False, created_at__lte=OuterRef('created_at'))
        .order_by('-created_at')
        .values('unit_price')[:1]
    )
    rows = (InventoryTransaction.objects
            .filter(household=household, change_type=CT.WASTED,
                    created_at__gte=last_start)
            .annotate(price_at=price_at)
            .values('item_id', 'item__name', 'item__unit',
                    'quantity_delta', 'price_at', 'created_at'))

    def bucket():
        return {'value': Decimal('0'), 'events': 0, 'unvalued_events': 0}

    this_m, last_m = bucket(), bucket()
    per_item = {}
    for r in rows:
        qty = abs(r['quantity_delta'])
        is_this = r['created_at'] >= this_start
        b = this_m if is_this else last_m
        b['events'] += 1
        if r['price_at'] is None:
            b['unvalued_events'] += 1
            value = None
        else:
            value = qty * r['price_at']
            b['value'] += value
        if is_this:
            it = per_item.setdefault(r['item_id'], {
                'item_id': r['item_id'], 'name': r['item__name'],
                'unit': r['item__unit'], 'quantity': Decimal('0'),
                'value': Decimal('0'), 'has_unvalued': False})
            it['quantity'] += qty
            if value is None:
                it['has_unvalued'] = True
            else:
                it['value'] += value

    def out(b):
        return {'value': float(b['value']), 'events': b['events'],
                'unvalued_events': b['unvalued_events']}

    top = sorted(per_item.values(), key=lambda i: i['value'], reverse=True)[:WASTE_TOP_ITEMS]
    for t in top:
        t['quantity'] = float(t['quantity'])
        t['value'] = float(t['value'])
    return {'this_month': out(this_m), 'last_month': out(last_m), 'top_items': top}


def stock_ledger(household):
    """One pass over the household's transactions.
    Returns (ref, last_at, last_price) dicts keyed by item_id:
      ref        = running balance right after the latest purchase/restock
      last_at    = time of the item's latest transaction
      last_price = latest recorded unit price on a stock-in
    """
    ref, last_at, last_price = {}, {}, {}
    balance = defaultdict(Decimal)
    rows = (InventoryTransaction.objects.filter(household=household)
            .order_by('item_id', 'created_at', 'id')
            .values_list('item_id', 'change_type', 'quantity_delta',
                         'unit_price', 'created_at'))
    for item_id, ctype, delta, price, at in rows:
        balance[item_id] += delta
        last_at[item_id] = at
        if ctype in STOCK_IN:
            ref[item_id] = balance[item_id]
            if price is not None:
                last_price[item_id] = price
    return ref, last_at, last_price


def low_stock(items, ledger, now):
    ref, last_at, last_price = ledger
    recent = now - timedelta(days=OUT_OF_STOCK_RECENT_DAYS)
    out = []
    for item in items:
        r = ref.get(item.id)
        if not r or r <= 0:
            continue                      # never stocked via a transaction: nothing to compare with
        qty = item.quantity
        if qty <= 0:
            if last_at[item.id] < recent:
                continue
            status = 'out'
        elif qty / r <= LOW_STOCK_RATIO:
            status = 'low'
        else:
            continue
        price = last_price.get(item.id)
        out.append({
            'item_id': item.id, 'name': item.name, 'unit': item.unit,
            'quantity': float(max(qty, 0)), 'reference_qty': float(r),
            'percent': round(float(max(qty, 0) / r * 100)),
            'status': status,
            'last_price': float(price) if price is not None else None,
        })
    out.sort(key=lambda x: (x['status'] != 'out', x['percent']))
    return out[:LOW_STOCK_MAX]


def use_first(items, ledger, today):
    _, _, last_price = ledger
    out = []
    for item in items:
        if item.expiry_date is None or item.quantity <= 0:
            continue
        days_left = (item.expiry_date - today).days
        if not (settings.EXPIRY_WINDOW_DAYS < days_left <= USE_FIRST_WINDOW_DAYS):
            continue                      # <= window is already card 1
        price = last_price.get(item.id)
        out.append({
            'item_id': item.id, 'name': item.name, 'unit': item.unit,
            'quantity': float(item.quantity),
            'expiry_date': item.expiry_date.isoformat(),
            'days_left': days_left,
            'value': float(item.quantity * price) if price is not None else None,
        })
    out.sort(key=lambda x: (x['days_left'], -(x['value'] or 0)))
    return out[:USE_FIRST_MAX]


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.localtime()
        household = Household.objects.filter(members=request.user).first()
        if household is None:
            return Response({
                'has_household': False,
                'price_changes': [],
                'waste': {'this_month': {'value': 0, 'events': 0, 'unvalued_events': 0},
                          'last_month': {'value': 0, 'events': 0, 'unvalued_events': 0},
                          'top_items': []},
            })
        items = list(Item.objects.filter(household=household))
        ledger = stock_ledger(household)
        return Response({
            'has_household': True,
            'generated_at': now.isoformat(),
            'price_changes': price_changes(household, now),
            'waste': waste_summary(household, now),
            'low_stock': low_stock(items, ledger, now),
            'user_first': use_first(items, ledger, timezone.localdate()),
            'budget': float(household.monthly_budget) if household.monthly_budget is not None else None,
            'is_owner': HouseholdMember.objects.filter(
                household=household, user=request.user, role=HouseholdMember.OWNER).exists(),
        })