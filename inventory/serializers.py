from rest_framework import serializers
from .models import Category, Item, InventoryTransaction

class CategorySerializer(serializers.ModelSerializer): 
    class Meta:
        model = Category
        fields = ['id', 'name', 'household']
        read_only_fields = ['household']

class ItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Item
        fields = [
            'id', 'name', 'quantity', 'unit', 'category', 'category_name',
            'household', 'expiry_date', 'image', 'notes', 'auto_decrement_amount', 'auto_decrement_interval_days', 'last_auto_decrement_at','created_at', 'updated_at'
        ]
        read_only_fields = ['household', 'created_at', 'updated_at', 'quantity', 'last_auto_decrement_at']

class InventoryTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryTransaction
        fields = [
            'id', 'item', 'change_type', 'quantity_delta', 'source', 'note', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate(self, data):
        item = data['item']
        delta = data['quantity_delta']
        resulting_quantity = item.quantity + delta

        if resulting_quantity < 0:
            raise serializers.ValidationError({
                'quantity_delta': (
                    f"insufficien stock. Currently quantity is {item.quantity}, "
                    f"this would result in {resulting_quantity}"
                )
            })
        
        return data