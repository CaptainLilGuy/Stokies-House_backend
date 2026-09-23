from rest_framework import serializers
from .models import Expense

class ExpenseSerializer(serializers.ModelSerializer):
    logged_by_username = serializers.CharField(source='logged_by.username', read_only=True)
    item_name = serializers.CharField(source='item.name', read_only=True, default=None)
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)

    class Meta:
        model = Expense
        fields = [
            'id', 'household', 'logged_by', 'logged_by_username',
            'item', 'item_name', 'category', 'category_name',
            'description', 'amount', 'date', 'source', 'created_at'
        ]
        read_only_fields = ['household', 'logged_by', 'created_at']
        extra_kwargs = {
            'item': {'required': False, 'allow_null': True},
            'category': {'required': False, 'allow_null': True},
        }