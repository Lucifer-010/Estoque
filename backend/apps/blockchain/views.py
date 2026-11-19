from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .models import BlockchainTransactionRecord
from .serializers import (
    BlockchainTransactionRecordSerializer,
    ContractStatusSerializer,
)
from .services import BlockchainService

class BlockchainTransactionRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BlockchainTransactionRecord.objects.all().select_related('order', 'batch').order_by('-created_at')
    serializer_class = BlockchainTransactionRecordSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['Soroban Blockchain & Escrow'],
        summary='Audit trail of all on-chain batch proofs, handovers, and escrow transactions'
    )
    def get_queryset(self):
        tx_type = self.request.query_params.get('tx_type')
        if tx_type:
            return self.queryset.filter(tx_type=tx_type)
        return self.queryset

class ContractStatusView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['Soroban Blockchain & Escrow'],
        summary='Soroban Smart Contract & Stellar Testnet configuration and status',
        responses={200: ContractStatusSerializer}
    )
    def get(self, request):
        service = BlockchainService()
        info = service.get_contract_info()
        return Response(info)

class EscrowLookupView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['Soroban Blockchain & Escrow'],
        summary='Lookup on-chain escrow state for a given purchase order id',
        responses={200: OpenApiResponse(description="Escrow status details")}
    )
    def get(self, request, order_id):
        from apps.orders.models import PurchaseOrder
        try:
            order = PurchaseOrder.objects.get(id=order_id)
            records = BlockchainTransactionRecord.objects.filter(order=order).values(
                'tx_type', 'tx_hash', 'status', 'created_at', 'amount'
            )
            return Response({
                'order_id': order.id,
                'po_number': order.po_number,
                'status': order.status,
                'total_amount_usdc': str(order.total_amount),
                'escrow_tx_hash': order.escrow_tx_hash,
                'release_tx_hash': order.release_tx_hash,
                'refund_tx_hash': order.refund_tx_hash,
                'handover_id': order.on_chain_handover_id,
                'blockchain_records': list(records)
            })
        except PurchaseOrder.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

