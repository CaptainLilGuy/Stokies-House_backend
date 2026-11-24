import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('households', '0003_household_monthly_budget'),
        ('inventory', '0006_alter_tag_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Receipt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('store_name', models.CharField(blank=True, max_length=100)),
                ('purchased_on', models.DateField()),
                ('total', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ('discount_total', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('fingerprint', models.CharField(blank=True, max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('household', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receipts', to='households.household')),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='receipts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-purchased_on', '-created_at'],
                'constraints': [
                    models.UniqueConstraint(
                        condition=models.Q(('fingerprint', ''), _negated=True),
                        fields=('household', 'fingerprint'),
                        name='unique_receipt_fingerprint_per_household'),
                ],
            },
        ),
        migrations.AddField(
            model_name='inventorytransaction',
            name='receipt',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transactions', to='inventory.receipt'),
        ),
        migrations.AddField(
            model_name='inventorytransaction',
            name='discount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='inventorytransaction',
            name='purchased_on',
            field=models.DateField(null=True),
        ),
        migrations.AddIndex(
            model_name='inventorytransaction',
            index=models.Index(fields=['item', 'purchased_on'], name='inv_txn_item_purchased_idx'),
        ),
    ]