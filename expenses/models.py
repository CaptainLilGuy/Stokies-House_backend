from django.db import models
from django.conf import settings
from households.models import Household
from inventory.models import Item, Category

class Expense(models.Model):
    class Source(models.TextChoices):
        OCR = 'ocr', 'OCR Scan'
        MANUAL = 'manual', 'Manual Entry'

    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='expenses')
    logged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='expenses')
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, related_name='expenses')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description} - Rp{self.amount}"