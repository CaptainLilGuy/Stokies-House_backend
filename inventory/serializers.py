from rest_framework import serializers
from households.models import Household
from .models import Category, Item, InventoryTransaction

class CategorySerializer(serializers.ModelSerializer): 
    class Meta:
        model = Category
        fields = ['id', 'name', 'household']
        read_only_fields = ['household']

class ItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    # Annotated in the view querysets; absent on create responses (DRF skips it).
    last_unit_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Item
        fields = [
            'id', 'name', 'quantity', 'unit', 'category', 'category_name',
            'household', 'expiry_date', 'image', 'notes', 'auto_decrement_amount',
            'auto_decrement_interval_days', 'last_auto_decrement_at',
            'last_unit_price', 'created_at', 'updated_at'
        ]
        read_only_fields = ['household', 'created_at', 'updated_at', 'quantity', 'last_auto_decrement_at']

class InventoryTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryTransaction
        fields = [
            'id', 'item', 'change_type', 'quantity_delta', 'unit_price',
            'source', 'note', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'unit_price': {'required': False, 'allow_null': True, 'min_value': 0},
        }

    def validate(self, data):
        ChangeType = InventoryTransaction.ChangeType
        request = self.context['request']
        item = data['item']

        # An item must belong to the caller's household (blocks cross-household writes)
        household = Household.objects.filter(members=request.user).first()
        if household is None or item.household_id != household.id:
            raise serializers.ValidationError({'item': 'Item not found in your household.'})

        change = data['change_type']
        delta = data['quantity_delta']
        price = data.get('unit_price')

        # Signed-delta convention: stock in is positive, stock out is negative
        if change in (ChangeType.PURCHASED, ChangeType.RESTOCKED) and delta <= 0:
            raise serializers.ValidationError(
                {'quantity_delta': 'Must be positive for purchases and restocks.'})
        if change in (ChangeType.CONSUMED, ChangeType.WASTED) and delta >= 0:
            raise serializers.ValidationError(
                {'quantity_delta': 'Must be negative for consumption and waste.'})

        # Price only makes sense when stock comes in
        if price is not None and change not in (ChangeType.PURCHASED, ChangeType.RESTOCKED):
            raise serializers.ValidationError(
                {'unit_price': 'Only allowed for purchases and restocks.'})

        resulting_quantity = item.quantity + delta
        if resulting_quantity < 0:
            raise serializers.ValidationError({
                'quantity_delta': (
                    f"Insufficient stock. Currently quantity is {item.quantity}, "
                    f"this would result in {resulting_quantity}"
                )
            })
        
        return data