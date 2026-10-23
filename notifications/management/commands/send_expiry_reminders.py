from datetime import date

from django.core.management.base import BaseCommand
from django.utils import timezone

from notifications.models import NotificationLog
from notifications.services import build_digest, items_by_user, send_to_tokens

KIND = NotificationLog.Kind.EXPIRY_DIGEST


class Command(BaseCommand):
    help = 'Send one expiry digest push per user with items expiring soon.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Print only; send nothing, log nothing.')
        parser.add_argument('--force', action='store_true', help='Ignore the once-per-day dedupe.')
        parser.add_argument('--user', help='Only this username.')
        parser.add_argument('--today', help='Simulate a date (YYYY-MM-DD).')

    def handle(self, *args, **opts):
        today = date.fromisoformat(opts['today']) if opts['today'] else timezone.localdate()
        self.stdout.write(f'Running for {today}')

        for user, items in items_by_user(today).items():
            if opts['user'] and user.username != opts['user']:
                continue
            title, body = build_digest(items, today)
            tokens = list(user.device_tokens.values_list('token', flat=True))

            if not opts['force'] and NotificationLog.objects.filter(
                    user=user, kind=KIND, sent_for=today).exists():
                self.stdout.write(f'[skip: already sent] {user.username}')
                continue
            if not tokens:
                self.stdout.write(f'[skip: no devices] {user.username}')
                continue
            if opts['dry_run']:
                self.stdout.write(f'[dry-run] {user.username} ({len(tokens)} device): {title} | {body}')
                continue

            ok, pruned = send_to_tokens(tokens, title, body)
            if ok:
                NotificationLog.objects.update_or_create(
                    user=user, kind=KIND, sent_for=today,
                    defaults={'title': title, 'body': body, 'item_count': len(items)})
            self.stdout.write(f'[sent] {user.username}: {ok}/{len(tokens)} delivered, {pruned} stale removed')