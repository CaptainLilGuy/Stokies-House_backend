from django.urls import path
from .views import HouseholdCreateView, HouseholdDetailView, JoinHouseholdView, MyHouseholdView

urlpatterns = [
    path('', HouseholdCreateView.as_view()),
    path('me/', MyHouseholdView.as_view()),
    path('<int:pk>/', HouseholdDetailView.as_view()),
    path('join/', JoinHouseholdView.as_view()),
]