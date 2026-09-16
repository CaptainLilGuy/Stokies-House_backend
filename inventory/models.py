from django.db import models
from django.conf import settings
from households.models import Household

class Category(models.Model):
    name = models.CharField(max_length=100)
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='categories')

    def __str__(self):
        return self.name
    
class Item(models.Model):
    name = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)
    unit = models.CharField(max_length=20, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='items')
    expiry_date = models.DateField(null=True, blank=True)
    image = models.ImageField(upload_to='item_images/', blank=True, null=True)
    notes = models.TextField(blank=True)
    auto_decrement_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    auto_decrement_interval_days = models.PositiveIntegerField(null=True, blank=True)
    last_auto_decrement_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
class InventoryTransaction(models.Model):
    class ChangeType(models.TextChoices):
        PURCHASED = 'purchased', 'Purchased'
        RESTOCKED = 'restocked', 'Restocked'
        CONSUMED = 'consumed', 'Consumed'
        WASTED = 'wasted', 'Wasted'
        ADJUSTED = 'adjusted', 'Adjusted'
    
    class Source(models.TextChoices):
        OCR = 'ocr', 'OCR Scan'
        MANUAL = 'manual', 'Manual Entry'
        AUTO = 'auto', 'Auto Decrement'

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='transactions')
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='inventory_transactions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name='inventory_transactions')
    change_type = models.CharField(max_length=20, choices=ChangeType.choices)
    quantity_delta = models.DecimalField(max_digits=10, decimal_places=2)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['item', 'created_at']),
            models.Index(fields=['household', 'change_type', 'created_at']),
        ]

    def __str__(self):
        return f"{self.item.name}: {self.quantity_delta} ({self.change_type})"