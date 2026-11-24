import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0008_backfill_purchased_on'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventorytransaction',
            name='purchased_on',
            field=models.DateField(default=django.utils.timezone.localdate),
        ),
    ]