from django.contrib import admin
from .models import InventoryTransaction, Item, Category, Tag

# Register your models here.

admin.site.register(InventoryTransaction)
admin.site.register(Item)
admin.site.register(Category)
admin.site.register(Tag)