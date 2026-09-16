from rest_framework import generics, permissions
from datetime import timedelta
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Category, Item, InventoryTransaction
from .serializers import CategorySerializer, ItemSerializer, InventoryTransactionSerializer
from households.models import Household
from decimal import Decimal, InvalidOperation
from .parser import parse_items, extract_total, extract_date, strip_header_noise

def get_user_household(user):
    return Household.objects.filter(members=user).first()

# CRUD Endpoints

class CategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        household = get_user_household(self.request.user)
        return Category.objects.filter(household=household)

    def perform_create(self, serializer):
        household = get_user_household(self.request.user)
        serializer.save(household=household)

class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        household = get_user_household(self.request.user)
        return Category.objects.filter(household=household)
    
    def perform_destroy(self, instance):
        print(f"Deleting item: {instance.name}")
        return super().perform_destroy(instance)

class ItemListCreateView(generics.ListCreateAPIView):
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        household = get_user_household(self.request.user)
        return Item.objects.filter(household=household).order_by('-updated_at')

    def perform_create(self, serializer):
        household = get_user_household(self.request.user)
        
        raw_qty = self.request.data.get('quantity')
        try:
            initial_qty = Decimal(str(raw_qty)) if raw_qty is not None else Decimal('0')
        except InvalidOperation:
            initial_qty = Decimal('0')

        with transaction.atomic():
            item = serializer.save(household=household)

            if initial_qty > 0:
                InventoryTransaction.objects.create(
                    item=item,
                    household=household,
                    user=self.request.user,
                    change_type= InventoryTransaction.ChangeType.PURCHASED,
                    quantity_delta=initial_qty,
                    source=InventoryTransaction.Source.MANUAL,
                    note='Initial stock on item creation',
                )
                Item.objects.filter(pk=item.pk).update(
                    quantity=F('quantity') + initial_qty
                )
                item.refresh_from_db(fields=['quantity'])

class ItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        household = get_user_household(self.request.user)
        return Item.objects.filter(household=household)
    
    def perform_update(self, serializer):
        print(f"Updating item: {serializer.instance.name}")
        return super().perform_update(serializer)

    def perform_destroy(self, instance):
        print(f"Deleting item: {instance.name}")
        return super().perform_destroy(instance)

class InventoryTransactionListCreateView(generics.ListCreateAPIView):
    serializer_class = InventoryTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        household = get_user_household(self.request.user)
        return InventoryTransaction.objects.filter(
            household = household
        ).select_related('item')
    
    def perform_create(self, serializer):
        household = get_user_household(self.request.user)
        with transaction.atomic():
            txn = serializer.save(
                household=household,
                user=self.request.user
            )
            Item.objects.filter(pk=txn.item.pk).update(
                quantity = F('quantity') + txn.quantity_delta
            )

#Action / Command Endpoints
class ProcessAutoDecrementsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        household = get_user_household(request.user)
        now = timezone.now()

        eligible_items = Item.objects.filter(
            household=household,
            auto_decrement_amount__isnull=False,
            auto_decrement_interval_days__isnull=False,
        )

        items_processed = []
        total_transaction_created = 0
        for item_id in eligible_items.values_list('id', flat=True):
            with transaction.atomic():
                # Lock the row for the duration of this item's processing
                item = Item.objects.select_for_update().get(pk=item_id)

                if item.auto_decrement_amount is None or item.auto_decrement_interval_days is None:
                    continue # re-check post-lock in case it changed concurrently
                
                reference_time = item.last_auto_decrement_at or item.created_at
                elapsed_days = (now - reference_time).days

                if elapsed_days <= 0:
                    continue
                
                pending_count = elapsed_days // item.auto_decrement_interval_days

                if pending_count == 0:
                    continue

                created_count = 0
                current_quantity = item.quantity

                for _ in range(pending_count):
                    if current_quantity - item.auto_decrement_amount < 0:
                        break # negative-quantity guard: stop, don't partial-decrement
                
                    InventoryTransaction.objects.create(
                        item=item,
                        household=item.household,
                        quantity_delta=item.auto_decrement_amount,
                        change_type='consumed',
                        source='auto'
                    )

                    Item.objects.filter(pk=item.pk).update(
                        quantity=F('quantity') - item.auto_decrement_amount
                    )

                    current_quantity -= item.auto_decrement_amount
                    created_count += 1

                if created_count > 0:
                    # last_auto_decrement_at advances by whole intervals actually
                    # consumed, not to `now` — see note below
                    item.last_auto_decrement_at = reference_time + timedelta(
                        days=created_count * item.auto_decrement_interval_days
                    )
                    item.save(update_fields=['last_auto_decrement_at'])

                    total_transaction_created += created_count
                    items_processed.append({
                        'item_id' : item.id,
                        'item_name' : item.name,
                        'transaction_created' : created_count,
                        'capped_by_zero_guard' : created_count < pending_count,
                    })

        return Response({
            'items_processed' : len(items_processed),
            'transactions_created' : total_transaction_created,
            'details' : items_processed,
        }, status=status.HTTP_200_OK)

class ParseReceiptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        raw_text = request.data.get('raw_text', '')
        if not raw_text.strip():
            return Response({'error': 'No text provided.'}, status=status.HTTP_400_BAD_REQUEST)

        raw_lines = [l for l in raw_text.split('\n') if l.strip()]
        lines = strip_header_noise(raw_lines)

        items, layout_used = parse_items(lines)

        return Response({
            'items': items,
            'layout_detected': layout_used,   # NEW — surface this so Flutter can show a hint if 'unrecognized'
            'total': extract_total(lines),
            'date': extract_date(raw_lines),
            'store_name': None,               # NEW — always None now; user fills this in manually
            'raw_text': raw_text,
        }, status=status.HTTP_200_OK)