from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .models import Product, InventoryBatch, StockMovement
from .serializers import (
    ProductSerializer,
    InventoryBatchSerializer,
    StockMovementSerializer,
    StockAdjustmentSerializer,
)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().select_related('supplier').prefetch_related('batches')
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['title', 'sku', 'category']
    filterset_fields = ['supplier', 'category', 'is_active']

    @extend_schema(tags=['Inventory & Products'], summary='List or create products in catalog')
    def get_queryset(self):
        supplier_id = self.request.query_params.get('supplier_id')
        if supplier_id:
            return self.queryset.filter(supplier_id=supplier_id)
        return self.queryset

class InventoryBatchViewSet(viewsets.ModelViewSet):
    queryset = InventoryBatch.objects.all().select_related('product', 'product__supplier').prefetch_related('movements')
    serializer_class = InventoryBatchSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        batch = serializer.save()
        # Record initial incoming stock movement
        StockMovement.objects.create(
            batch=batch,
            movement_type=StockMovement.MovementType.INCOMING,
            quantity=batch.initial_quantity,
            remaining_balance=batch.available_quantity,
            reference=f"INITIAL-{batch.batch_number}",
            actor=self.request.user if self.request.user.is_authenticated else None,
            notes="Initial batch registration"
        )

    @extend_schema(
        tags=['Inventory & Products'],
        summary='Adjust batch inventory quantity and record audit movement',
        request=StockAdjustmentSerializer,
        responses={200: InventoryBatchSerializer}
    )
    @action(detail=True, methods=['post'], url_path='adjust-stock')
    def adjust_stock(self, request, pk=None):
        batch = self.get_object()
        serializer = StockAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        change = serializer.validated_data['quantity_change']
        reason = serializer.validated_data.get('reason', 'Stock adjustment')

        new_avail = batch.available_quantity + change
        if new_avail < 0:
            return Response(
                {'error': f"Insufficient stock. Available: {batch.available_quantity}, requested reduction: {-change}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        batch.available_quantity = new_avail
        batch.save(update_fields=['available_quantity', 'updated_at'])

        StockMovement.objects.create(
            batch=batch,
            movement_type=StockMovement.MovementType.ADJUSTMENT,
            quantity=change,
            remaining_balance=batch.available_quantity,
            reference="AUDIT-ADJUST",
            actor=request.user if request.user.is_authenticated else None,
            notes=reason
        )

        return Response(InventoryBatchSerializer(batch).data)

    @extend_schema(
        tags=['Inventory & Products'],
        summary='Trigger Soroban on-chain batch proof registration',
        responses={200: OpenApiResponse(description="Anchored batch proof result")}
    )
    @action(detail=True, methods=['post'], url_path='register-proof')
    def register_proof(self, request, pk=None):
        batch = self.get_object()
        from apps.blockchain.services import BlockchainService

        service = BlockchainService()
        result = service.register_batch_proof(batch)
        return Response(result)

class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockMovement.objects.all().select_related('batch', 'batch__product', 'actor').order_by('-created_at')
    serializer_class = StockMovementSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(tags=['Inventory & Products'], summary='Audit log of all stock movements and adjustments')
    def get_queryset(self):
        batch_id = self.request.query_params.get('batch_id')
        if batch_id:
            return self.queryset.filter(batch_id=batch_id)
        return self.queryset

