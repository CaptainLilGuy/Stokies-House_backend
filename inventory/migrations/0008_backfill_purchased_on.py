from django.db import migrations
from django.db.models.functions import TruncDate


def backfill(apps, schema_editor):
    Txn = apps.get_model('inventory', 'InventoryTransaction')
    # TruncDate uses the current timezone (Asia/Jakarta per settings), so dates match local days.
    Txn.objects.filter(purchased_on__isnull=True).update(purchased_on=TruncDate('created_at'))


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0007_receipt_and_transaction_fields'),
    ]

    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]