from rest_framework import serializers
from .models import Expense

class ExpenseSerializer(serializers.ModelSerializer):
    logged_by_username = serializers.CharField(source='Logged_by.username', read_only=True)
    item_name = serializers.CharField(source='item.name', read_only=True)

    class Meta:
        model = Expense
        fields = [
            'id', 'household', 'logged_by', 'logged_by_username',
            'item', 'item_name', 'description', 'amount', 'date', 'created_at'
        ]
        read_only_fields = ['household', 'logged_by', 'created_at']