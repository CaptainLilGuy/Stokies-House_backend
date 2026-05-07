from rest_framework import generics, permissions
from .models import Expense
from .serializers import ExpenseSerializer
from households.models import Household

def get_user_household(user):
    return Household.objects.filter(members=user).first()

class ExpenseListCreateView(generics.ListCreateAPIView):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        household = get_user_household(self.request.user)
        return Expense.objects.filter(household=household).order_by('-date')

    def perform_create(self, serializer):
        household = get_user_household(self.request.user)
        serializer.save(household=household, logged_by=self.request.user)

class ExpenseDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        household = get_user_household(self.request.user)
        return Expense.objects.filter(household=household)