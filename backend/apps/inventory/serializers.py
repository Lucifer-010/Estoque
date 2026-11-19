from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Product, InventoryBatch, StockMovement

class ProductSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.company_name', read_only=True)
    total_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'supplier', 'supplier_name', 'sku', 'title', 'category',
            'description', 'unit_of_measure', 'unit_price', 'total_stock',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    @extend_schema_field(serializers.IntegerField())
    def get_total_stock(self, obj):
        return sum(b.available_quantity for b in obj.batches.all())

class StockMovementSerializer(serializers.ModelSerializer):
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True)
    actor_username = serializers.CharField(source='actor.username', read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            'id', 'batch', 'batch_number', 'movement_type', 'quantity',
            'remaining_balance', 'reference', 'actor', 'actor_username',
            'notes', 'created_at'
        ]
        read_only_fields = ['id', 'remaining_balance', 'created_at']

class InventoryBatchSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    product_title = serializers.CharField(source='product.title', read_only=True)
    movements = StockMovementSerializer(many=True, read_only=True)

    class Meta:
        model = InventoryBatch
        fields = [
            'id', 'product', 'product_sku', 'product_title', 'batch_number',
            'manufacture_date', 'expiry_date', 'initial_quantity',
            'available_quantity', 'reserved_quantity', 'unit_cost',
            'batch_hash', 'on_chain_registered', 'on_chain_tx_hash',
            'on_chain_registered_at', 'movements', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'batch_hash', 'on_chain_registered',
            'on_chain_tx_hash', 'on_chain_registered_at', 'created_at', 'updated_at'
        ]

class StockAdjustmentSerializer(serializers.Serializer):
    quantity_change = serializers.IntegerField(
        help_text="Positive number to add stock, negative to subtract stock"
    )
    reason = serializers.CharField(required=False, default="Manual adjustment")
