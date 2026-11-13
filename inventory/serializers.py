from rest_framework import serializers
from households.models import Household
from .models import Category, Item, InventoryTransaction, Tag

def _household_of(request):
    return Household.objects.filter(members=request.user).first()    

class CategorySerializer(serializers.ModelSerializer): 
    class Meta:
        model = Category
        fields = ['id', 'name', 'household']
        read_only_fields = ['household']

class TagSerializer(serializers.ModelSerializer):
    item_count = serializers.IntegerField(read_only=True)

    class Meta:
        model =  Tag
        fields = ['id', 'name', 'item_count']

    def validate_name(self, value):
        value = ' '.join(value.split())
        if not value:
            raise serializers.ValidationError('Tag name is required.')
        household = _household_of(self.context['request'])
        clash = Tag.objects.filter(household=household, name__iexact=value)
        if self.instance is not None:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise serializers.ValidationError('A tag with this name is already exist.')
        return value

class TagBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

class ItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    # Annotated in the view querysets; absent on create responses (DRF skips it).
    last_unit_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True)
    tags = TagBriefSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), source='tags',
        write_only=True, required=False
    )

    class Meta:
        model = Item
        fields = [
            'id', 'name', 'quantity', 'unit', 'category', 'category_name',
            'tags', 'tag_ids',
            'household', 'expiry_date', 'image', 'notes', 'auto_decrement_amount',
            'auto_decrement_interval_days', 'last_auto_decrement_at',
            'last_unit_price', 'created_at', 'updated_at'
        ]
        read_only_fields = ['household', 'created_at', 'updated_at', 'quantity', 'last_auto_decrement_at']

    def validate_tag_ids(self, tags):
        household = _household_of(self.context['request'])
        if household is None or any(t.household.id != household.id for t in tags):
            raise serializers.ValidationError('Tag not found in your household.')
        return tags

    def validate_category(self, category):
        household = _household_of(self.context['request'])
        if category is not None and (household is None or category.household_id != household.id):
         raise serializers.ValidationError('Category not found in your household.')
        return category

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

class TransactionHistorySerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_unit = serializers.CharField(source='item.unit', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = InventoryTransaction
        fields = [
            'id', 'item', 'item_name', 'item_unit', 'change_type',
            'quantity_data', 'unit_price', 'source', 'note',
            'created_at', 'username'
        ]