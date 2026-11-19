from django.utils import timezone
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .models import PurchaseOrder, OrderItem
from .serializers import (
    PurchaseOrderSerializer,
    CreatePurchaseOrderSerializer,
    DispatchOrderSerializer,
    ReceiptOrderSerializer,
)
from apps.inventory.models import StockMovement

class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all().select_related('retailer', 'supplier').prefetch_related('items', 'items__product', 'items__batch')
    serializer_class = PurchaseOrderSerializer
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePurchaseOrderSerializer
        return PurchaseOrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = CreatePurchaseOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(PurchaseOrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=['Purchase Orders'],
        summary='Fund purchase order using simulated USDC in Soroban escrow',
        responses={200: OpenApiResponse(description="Escrow funding transaction record")}
    )
    @action(detail=True, methods=['post'], url_path='fund-escrow')
    def fund_escrow(self, request, pk=None):
        order = self.get_object()
        if order.status not in [PurchaseOrder.Status.PENDING_ESCROW, PurchaseOrder.Status.DRAFT]:
            return Response(
                {'error': f"Order cannot be funded in status '{order.status}'. Already funded or closed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        from apps.blockchain.services import BlockchainService
        service = BlockchainService()
        result = service.fund_escrow(order)
        return Response(result)

    @extend_schema(
        tags=['Purchase Orders'],
        summary='Record supplier dispatch, generate tracking & record on-chain handover',
        request=DispatchOrderSerializer,
        responses={200: PurchaseOrderSerializer}
    )
    @action(detail=True, methods=['post'], url_path='dispatch')
    def dispatch_order(self, request, pk=None):
        order = self.get_object()
        if order.status != PurchaseOrder.Status.ESCROW_FUNDED:
            return Response(
                {'error': f"Order must be ESCROW_FUNDED before dispatch. Current status: {order.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = DispatchOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order.tracking_number = serializer.validated_data['tracking_number']
        order.shipping_carrier = serializer.validated_data.get('shipping_carrier', 'DHL Express')
        order.delivery_notes = serializer.validated_data.get('notes', '')
        order.dispatched_at = timezone.now()
        order.status = PurchaseOrder.Status.DISPATCHED
        order.save()

        # Update inventory batch stock movements to DISPATCHED
        for item in order.items.all():
            if item.batch:
                item.batch.reserved_quantity = max(0, item.batch.reserved_quantity - item.quantity)
                item.batch.save(update_fields=['reserved_quantity', 'updated_at'])

                StockMovement.objects.create(
                    batch=item.batch,
                    movement_type=StockMovement.MovementType.DISPATCHED,
                    quantity=-item.quantity,
                    remaining_balance=item.batch.available_quantity,
                    reference=f"DISPATCH-{order.po_number}",
                    actor=request.user if request.user.is_authenticated else None,
                    notes=f"Dispatched tracking: {order.tracking_number}"
                )

        # Trigger on-chain handover recording
        from apps.blockchain.services import BlockchainService
        service = BlockchainService()
        handover_res = service.record_handover(order)
        order.refresh_from_db()

        return Response({
            'order': PurchaseOrderSerializer(order).data,
            'blockchain_handover': handover_res
        })

    @extend_schema(
        tags=['Purchase Orders'],
        summary='Record retailer receipt, acknowledge custody on-chain & release escrow payment to supplier',
        request=ReceiptOrderSerializer,
        responses={200: OpenApiResponse(description="Delivery confirmed and payment released")}
    )
    @action(detail=True, methods=['post'], url_path='confirm-receipt')
    def confirm_receipt(self, request, pk=None):
        order = self.get_object()
        if order.status != PurchaseOrder.Status.DISPATCHED:
            return Response(
                {'error': f"Order must be in DISPATCHED status to confirm receipt. Current status: {order.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ReceiptOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order.delivered_at = timezone.now()
        notes = serializer.validated_data.get('delivery_notes', '')
        if notes:
            order.delivery_notes = f"{order.delivery_notes} | Receipt Note: {notes}".strip()
        order.status = PurchaseOrder.Status.DELIVERED
        order.save()

        # Execute Soroban custody acknowledgment & escrow release
        from apps.blockchain.services import BlockchainService
        service = BlockchainService()

        # 1. Acknowledge on-chain custody
        ack_res = service.acknowledge_custody(order)

        # 2. Release Soroban escrow payment to supplier
        release_res = service.release_escrow(order)

        order.status = PurchaseOrder.Status.COMPLETED
        order.save()

        return Response({
            'message': 'Delivery confirmed, custody acknowledged on-chain, and escrow released to supplier',
            'order': PurchaseOrderSerializer(order).data,
            'custody_acknowledgment': ack_res,
            'escrow_release': release_res
        })

    @extend_schema(
        tags=['Purchase Orders'],
        summary='Pre-dispatch cancellation and escrow refund back to retailer',
        responses={200: OpenApiResponse(description="Order cancelled and escrow refunded")}
    )
    @action(detail=True, methods=['post'], url_path='cancel-refund')
    def cancel_and_refund(self, request, pk=None):
        order = self.get_object()
        if order.status not in [PurchaseOrder.Status.PENDING_ESCROW, PurchaseOrder.Status.ESCROW_FUNDED]:
            return Response(
                {'error': f"Cannot cancel order in status '{order.status}'. Eligible only before dispatch."},
                status=status.HTTP_400_BAD_REQUEST
            )

        was_funded = (order.status == PurchaseOrder.Status.ESCROW_FUNDED)

        # Release reserved inventory back to available stock
        for item in order.items.all():
            if item.batch:
                item.batch.reserved_quantity = max(0, item.batch.reserved_quantity - item.quantity)
                item.batch.available_quantity += item.quantity
                item.batch.save(update_fields=['available_quantity', 'reserved_quantity', 'updated_at'])

                StockMovement.objects.create(
                    batch=item.batch,
                    movement_type=StockMovement.MovementType.RELEASED,
                    quantity=item.quantity,
                    remaining_balance=item.batch.available_quantity,
                    reference=f"CANCEL-{order.po_number}",
                    actor=request.user if request.user.is_authenticated else None,
                    notes=f"Order {order.po_number} cancelled before dispatch"
                )

        refund_result = None
        if was_funded:
            from apps.blockchain.services import BlockchainService
            service = BlockchainService()
            refund_result = service.refund_escrow(order)
            order.status = PurchaseOrder.Status.REFUNDED
        else:
            order.status = PurchaseOrder.Status.CANCELLED

        order.save()

        return Response({
            'message': 'Order successfully cancelled and inventory released.',
            'order': PurchaseOrderSerializer(order).data,
            'blockchain_refund': refund_result
        })

