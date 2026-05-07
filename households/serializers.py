from rest_framework import serializers
from .models import Household
from users.serializers import UserSerializer

class HouseholdSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Household
        fields = ['id', 'name', 'invite_code', 'created_by', 'members', 'created_at']
        read_only_fields = ['invite_code', 'created_by', 'created_at']