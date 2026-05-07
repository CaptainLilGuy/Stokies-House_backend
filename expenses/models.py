from django.db import models
from users.models import User
from households.models import Household
from inventory.models import Item

class Expense(models.Model):
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='expenses')
    logged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='expenses')
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, related_name='expenses')
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description} - Rp{self.amount}"