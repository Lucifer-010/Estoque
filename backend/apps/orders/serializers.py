from rest_framework import serializers
from decimal import Decimal
from .models import PurchaseOrder, OrderItem
from apps.inventory.models import Product, InventoryBatch, StockMovement

class OrderItemSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source='product.title', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_title', 'product_sku',
            'batch', 'batch_number', 'quantity', 'unit_price', 'subtotal'
        ]
        read_only_fields = ['id', 'subtotal']

class OrderItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'batch', 'quantity', 'unit_price']
        extra_kwargs = {
            'unit_price': {'required': False}
        }

class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    retailer_name = serializers.CharField(source='retailer.business_name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.company_name', read_only=True)
    retailer_wallet = serializers.CharField(source='retailer.stellar_wallet_address', read_only=True)
    supplier_payout_wallet = serializers.CharField(source='supplier.stellar_payout_address', read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'po_number', 'retailer', 'retailer_name', 'retailer_wallet',
            'supplier', 'supplier_name', 'supplier_payout_wallet', 'status',
            'total_amount', 'currency', 'escrow_tx_hash', 'release_tx_hash',
            'refund_tx_hash', 'on_chain_handover_id', 'handover_tx_hash',
            'tracking_number', 'shipping_carrier', 'dispatched_at',
            'delivered_at', 'delivery_notes', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'po_number', 'status', 'total_amount', 'escrow_tx_hash',
            'release_tx_hash', 'refund_tx_hash', 'on_chain_handover_id',
            'handover_tx_hash', 'dispatched_at', 'delivered_at', 'created_at', 'updated_at'
        ]

class CreatePurchaseOrderSerializer(serializers.Serializer):
    retailer = serializers.IntegerField()
    supplier = serializers.IntegerField()
    items = OrderItemCreateSerializer(many=True)

    def create(self, validated_data):
        from apps.accounts.models import RetailerProfile, SupplierProfile

        retailer = RetailerProfile.objects.get(id=validated_data['retailer'])
        supplier = SupplierProfile.objects.get(id=validated_data['supplier'])
        items_data = validated_data['items']

        order = PurchaseOrder.objects.create(
            retailer=retailer,
            supplier=supplier,
            status=PurchaseOrder.Status.PENDING_ESCROW
        )

        total = Decimal('0.00')
        for item_data in items_data:
            product = item_data['product']
            batch = item_data.get('batch')
            qty = item_data['quantity']
            unit_price = item_data.get('unit_price') or product.unit_price

            # If batch not provided, select first available batch of that product
            if not batch:
                batch = product.batches.filter(available_quantity__gte=qty).first()

            if batch:
                # Reserve stock
                if batch.available_quantity < qty:
                    raise serializers.ValidationError(
                        f"Insufficient available quantity in batch {batch.batch_number}. Available: {batch.available_quantity}, requested: {qty}"
                    )
                batch.available_quantity -= qty
                batch.reserved_quantity += qty
                batch.save(update_fields=['available_quantity', 'reserved_quantity', 'updated_at'])

                StockMovement.objects.create(
                    batch=batch,
                    movement_type=StockMovement.MovementType.RESERVED,
                    quantity=qty,
                    remaining_balance=batch.available_quantity,
                    reference=order.po_number,
                    notes=f"Reserved for {order.po_number}"
                )

            item = OrderItem.objects.create(
                order=order,
                product=product,
                batch=batch,
                quantity=qty,
                unit_price=unit_price
            )
            total += item.subtotal

        order.total_amount = total
        order.save(update_fields=['total_amount'])
        return order

class DispatchOrderSerializer(serializers.Serializer):
    tracking_number = serializers.CharField(max_length=100)
    shipping_carrier = serializers.CharField(max_length=100, default='DHL Express')
    notes = serializers.CharField(required=False, allow_blank=True)

class ReceiptOrderSerializer(serializers.Serializer):
    delivery_notes = serializers.CharField(required=False, allow_blank=True)

