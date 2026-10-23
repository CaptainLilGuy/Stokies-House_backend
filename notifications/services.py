from collections import defaultdict
from datetime import timedelta

import firebase_admin
from django.conf import settings
from firebase_admin import credentials, messaging

from households.models import HouseholdMember
from inventory.models import Item
from users.models import DeviceToken


def _init_firebase():
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app(credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH))


def days_label(days_left):
    if days_left < 0:
        return f'lewat {-days_left} hari'
    if days_left == 0:
        return 'hari ini'
    if days_left == 1:
        return 'besok'
    return f'{days_left} hari'


def items_by_user(today):
    """Return {user: [items]} for items expiring soon, across all households."""
    items = (Item.objects
             .filter(expiry_date__isnull=False, quantity__gt=0,
                     expiry_date__lte=today + timedelta(days=settings.EXPIRY_WINDOW_DAYS),
                     expiry_date__gte=today - timedelta(days=settings.EXPIRED_GRACE_DAYS))
             .order_by('expiry_date'))
    by_household = defaultdict(list)
    for item in items:
        by_household[item.household_id].append(item)

    by_user = defaultdict(list)
    for hid, hitems in by_household.items():
        for m in HouseholdMember.objects.filter(household_id=hid).select_related('user'):
            by_user[m.user].extend(hitems)
    for lst in by_user.values():
        lst.sort(key=lambda i: i.expiry_date)
    return by_user


def build_digest(items, today):
    shown = [f'{i.name} ({days_label((i.expiry_date - today).days)})' for i in items[:3]]
    body = f'{len(items)} barang: ' + ', '.join(shown)
    if len(items) > 3:
        body += f' dan {len(items) - 3} lainnya'
    return 'Barang hampir kedaluwarsa', body


def send_to_tokens(tokens, title, body):
    """Send one message to all tokens. Returns (success_count, pruned_count)."""
    _init_firebase()
    message = messaging.MulticastMessage(
        tokens=tokens,
        notification=messaging.Notification(title=title, body=body),
        data={'type': 'expiry_digest', 'route': '/dashboard'},
        android=messaging.AndroidConfig(priority='high'),
    )
    response = messaging.send_each_for_multicast(message)
    stale = [t for t, r in zip(tokens, response.responses)
             if not r.success and isinstance(
                 r.exception, (messaging.UnregisteredError, messaging.SenderIdMismatchError))]
    if stale:
        DeviceToken.objects.filter(token__in=stale).delete()
    return response.success_count, len(stale)