from django.urls import path
from .views import CategoryListCreateView, CategoryDetailView, TagListCreateView, TagDetailView, ItemListCreateView, ItemDetailView, InventoryTransactionListCreateView, ProcessAutoDecrementsView, ParseReceiptView, TransactionHistoryView

urlpatterns = [
    path('categories/', CategoryListCreateView.as_view()),
    path('categories/<int:pk>/', CategoryDetailView.as_view()),
    path('tags/', TagListCreateView.as_view()),
    path('tags/<int:pk>/', TagDetailView.as_view()),
    path('items/', ItemListCreateView.as_view()),
    path('items/<int:pk>/', ItemDetailView.as_view()),
    path('transactions/', InventoryTransactionListCreateView.as_view()),
    path('process-auto-decrements/', ProcessAutoDecrementsView.as_view()),
    path('ocr-parse/', ParseReceiptView.as_view()),
    path('transaction/history/', TransactionHistoryView.as_view()),
]