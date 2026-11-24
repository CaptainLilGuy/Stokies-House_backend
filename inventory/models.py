from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils import timezone
from django.conf import settings
from households.models import Household

class Receipt(models.Model):
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='receipts')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='receipts')
    store_name = models.CharField(max_length=100, blank=True)
    purchased_on = models.DateField()
    total = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    discount_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    # Hash of store|date|total|items, used to catch the same receipt scanned twice.
    fingerprint = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-purchased_on', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['household', 'fingerprint'],
                condition=~Q(fingerprint=''),
                name='unique_receipt_fingerprint_per_household',
            ),
        ]

    def __str__(self):
        return f"{self.store_name or 'Receipt'} {self.purchased_on}"

class Category(models.Model):
    name = models.CharField(max_length=100)
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='categories')

    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=300) #SAMAIN KAYAK DI FRONTEND
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='tags')

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower('name'), 'household', name='unique_tag_name_per_household_ci'),
        ]

    def __str__(self):
        return self.name
    
class Item(models.Model):
    name = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)
    unit = models.CharField(max_length=20, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    tags = models.ManyToManyField(Tag, blank=True, related_name='items')
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
    receipt = models.ForeignKey(
        Receipt, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    change_type = models.CharField(max_length=20, choices=ChangeType.choices)
    quantity_delta = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    # Total voucher/discount for this line (not per unit), as the Indomaret parser reports it.
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # Real-world date of the event (receipt date for scans). Use this, not created_at, for price math.
    purchased_on = models.DateField(default=timezone.localdate)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['item', 'created_at']),
            models.Index(fields=['household', 'change_type', 'created_at']),
            models.Index(fields=['item', 'purchased_on'], name='inv_txn_item_purchased_idx'),
        ]

    def __str__(self):
        return f"{self.item.name}: {self.quantity_delta} ({self.change_type})"