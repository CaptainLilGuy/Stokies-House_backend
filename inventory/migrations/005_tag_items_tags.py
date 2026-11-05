import django.db.models.deletion
import django.db.models.functions.text
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('households', '0002_household_created_by_householdmember_and_more'),
        ('inventory', '0004_inventorytransaction_unit_price'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('household', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tags', to='households.household')),
            ],
        ),
        migrations.AddConstraint(
            model_name='tag',
            constraint=models.UniqueConstraint(django.db.models.functions.text.Lower('name'), models.F('household'), name='unique_tag_name_per_household_ci'),
        ),
        migrations.AddField(
            model_name='item',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='items', to='inventory.tag'),
        ),
    ]