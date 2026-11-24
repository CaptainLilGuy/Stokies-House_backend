import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0004_expense_category_expense_source'),
        ('inventory', '0007_receipt_and_transaction_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='expense',
            name='receipt',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='expenses', to='inventory.receipt'),
        ),
    ]