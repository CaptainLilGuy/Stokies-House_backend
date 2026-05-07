from rest_framework import serializers
from .models import Category, Item

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
            'household', 'expiry_date', 'image', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['household', 'created_at', 'updated_at']