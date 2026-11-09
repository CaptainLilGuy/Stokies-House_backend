from django.urls import path
from .views import HouseholdCreateView, HouseholdDetailView, JoinHouseholdView, MyHouseholdView, HouseholdBudgetView, LeaveHouseholdView, RemoveMemberView, TransferOwnershipView

urlpatterns = [
    path('create/', HouseholdCreateView.as_view()),
    path('me/', MyHouseholdView.as_view()),
    path('me/budget/', HouseholdBudgetView.as_view()),
    path('join/', JoinHouseholdView.as_view()),
    path('leave/', LeaveHouseholdView.as_view()),
    path('<int:pk>/', HouseholdDetailView.as_view()),
    path('<int:pk>/members/<int:user_id>/', RemoveMemberView.as_view()),
    path('<int:pk>/transfer-owner/', TransferOwnershipView.as_view()),
]