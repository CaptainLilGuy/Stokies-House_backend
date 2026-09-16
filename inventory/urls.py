from django.urls import path
from .views import CategoryListCreateView, CategoryDetailView, ItemListCreateView, ItemDetailView, InventoryTransactionListCreateView, ProcessAutoDecrementsView, ParseReceiptView

urlpatterns = [
    path('categories/', CategoryListCreateView.as_view()),
    path('categories/<int:pk>/', CategoryDetailView.as_view()),
    path('items/', ItemListCreateView.as_view()),
    path('items/<int:pk>/', ItemDetailView.as_view()),
    path('transactions/', InventoryTransactionListCreateView.as_view()),
    path('process-auto-decrements/', ProcessAutoDecrementsView.as_view()),
    path('ocr-parse/', ParseReceiptView.as_view()),
]