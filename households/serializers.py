from rest_framework import serializers
from .models import Household, HouseholdMember
from users.serializers import UserSerializer

class HouseholdMemberSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='user.id')
    name = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email')
    role = serializers.CharField()

    class Meta:
        model = HouseholdMember
        fields = ['id', 'name', 'email', 'role']

class HouseholdSerializer(serializers.ModelSerializer):
    members = HouseholdMemberSerializer(source='householdmember_set', many=True, read_only=True)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Household
        fields = ['id', 'name', 'invite_code', 'created_by', 'members', 'created_at']
        read_only_fields = ['invite_code', 'created_by', 'created_at']