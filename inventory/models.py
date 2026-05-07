from django.db import models
from households.models import Household

class Category(models.Model):
    name = models.CharField(max_length=100)
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='categories')

    def __str__(self):
        return self.name
    
class Item(models.Model):
    name = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit = models.CharField(max_length=20, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='items')
    expiry_date = models.DateField(null=True, blank=True)
    image = models.ImageField(upload_to='item_images/', blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name