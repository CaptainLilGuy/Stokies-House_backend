from rest_framework import generics, permissions
from .models import Category, Item
from .serializers import CategorySerializer, ItemSerializer
from households.models import Household

def get_user_household(user):
    return Household.objects.filter(members=user).first()

class CategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        household = get_user_household(self.request.user)
        return Category.objects.filter(household=household)

    def perform_create(self, serializer):
        household = get_user_household(self.request.user)
        serializer.save(household=household)

class ItemListCreateView(generics.ListCreateAPIView):
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        household = get_user_household(self.request.user)
        return Item.objects.filter(household=household).order_by('-updated_at')

    def perform_create(self, serializer):
        household = get_user_household(self.request.user)
        serializer.save(household=household)

class ItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        household = get_user_household(self.request.user)
        return Item.objects.filter(household=household)