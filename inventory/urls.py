from django.urls import path
from .views import CategoryListCreateView, ItemListCreateView, ItemDetailView

urlpatterns = [
    path('categories/', CategoryListCreateView.as_view()),
    path('items/', ItemListCreateView.as_view()),
    path('items/<int:pk>/', ItemDetailView.as_view()),
]