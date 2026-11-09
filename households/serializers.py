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
    my_role = serializers.SerializerMethodField()

    class Meta:
        model = Household
        fields = ['id', 'name', 'invite_code', 'created_by', 'members', 'created_at', 'monthly_budget', 'my_role']
        read_only_fields = ['invite_code', 'created_by', 'created_at', 'monthly_budget']

    def get_my_role(self, obj):
        request = self.context.get('request')
        if request is None:
            return None
        m = obj.householdmember_set.filter(user=request.user).first()
        return m.role if m else None


class BudgetSerializer(serializers.Serializer):
    monthly_budget = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=0, allow_null = True
    )