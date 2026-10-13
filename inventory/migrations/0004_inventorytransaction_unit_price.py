from django.db import migrations, models
 
 
class Migration(migrations.Migration):
 
    dependencies = [
        ('inventory', '0003_alter_inventorytransaction_change_type'),
    ]
 
    operations = [
        migrations.AddField(
            model_name='inventorytransaction',
            name='unit_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
    ]
 