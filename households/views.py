from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Household, HouseholdMember
from .serializers import HouseholdSerializer, BudgetSerializer
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied


def membership_of(user):
    return (HouseholdMember.objects.filter(user=user)
            .select_related('household').first())


def require_owner(user, household):
    ok = HouseholdMember.objects.filter(
        household=household, user=user, role=HouseholdMember.OWNER).exists()
    if not ok:
        raise PermissionDenied('Only the household owner can do this.')



class HouseholdCreateView(generics.CreateAPIView):
    serializer_class = HouseholdSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            household = serializer.save(created_by=request.user)
            HouseholdMember.objects.create(
                household=household,
                user=request.user,
                role=HouseholdMember.OWNER
            )
            return Response(HouseholdSerializer(household).data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class HouseholdDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = HouseholdSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Household.objects.filter(members=self.request.user)

    def update(self, request, *args, **kwargs):
        require_owner(request.user, self.get_object())
        return super().update(request, *args, **kwargs)

    
class JoinHouseholdView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        code = request.data.get('invite_code', '').upper()
        try:
            household = Household.objects.get(invite_code=code)
        except Household.DoesNotExist:
            return Response({'error': 'Invalid invite code'}, status=400)

        current = membership_of(request.user)
        if current and current.household_id != household.id:
            return Response({'error': 'Leave your current household first.'}, status=400)

        HouseholdMember.objects.get_or_create(
            household=household, user=current.user,
            defaults={'role': HouseholdMember.MEMBER})
        return Response(HouseholdSerializer(household, context={'request': request}).data)


class RemoveMemberView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk, user_id):
        household = get_object_or_404(Household, pk=pk, members=request.user)
        require_owner(request.user, household)
        if user_id == request.user.id:
            return Response({'error': 'Use "leave" to exit your own household.'}, status=400)
        target = get_object_or_404(HouseholdMember, household=household, user_id=user_id)
        target.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LeaveHouseholdView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        with transaction.atomic():
            m = membership_of(request.user)
            if m is None:
                return Response({'error': 'You are not in a household.'}, status=404)
            others = HouseholdMember.objects.filter(household=m.household).exclude(pk=m.pk)
            if m.role == HouseholdMember.OWNER and others.exists():
                return Response(
                    {'error': 'Transfer ownership to another member before leaving.'},
                    status=400)
            household, last_one = m.household, not others.exists()
            m.delete()
            if last_one:
                household.delete()   # cascades items, tags, expenses
        return Response(status=status.HTTP_204_NO_CONTENT)


class TransferOwnershipView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        household = get_object_or_404(Household, pk=pk, members=request.user)
        require_owner(request.user, household)
        target = get_object_or_404(
            HouseholdMember, household=household, user_id=request.data.get('user_id'))
        with transaction.atomic():
            HouseholdMember.objects.filter(
                household=household, user=request.user).update(role=HouseholdMember.MEMBER)
            target.role = HouseholdMember.OWNER
            target.save(update_fields=['role'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class HouseholdBudgetView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        m = membership_of(request.user)
        if m is None:
            return Response({'error': 'Not in a household'}, status=404)
        require_owner(request.user, m.household)
        s = BudgetSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        m.household.monthly_budget = s.validated_data['monthly_budget']
        m.household.save(update_fields=['monthly_budget'])
        return Response({'monthly_budget': s.validated_data['monthly_budget']})


class MyHouseholdView(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        household = Household.objects.filter(members=request.user).first()
        if not household:
            return Response({'error': 'Not in a household'}, status=404)
        return Response(HouseholdSerializer(household, context={'request': request}).data)