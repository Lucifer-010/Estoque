from django.contrib import admin
from .models import Product, InventoryBatch, StockMovement

class InventoryBatchInline(admin.TabularInline):
    model = InventoryBatch
    extra = 0
    fields = ('batch_number', 'manufacture_date', 'expiry_date', 'initial_quantity', 'available_quantity', 'on_chain_registered')
    readonly_fields = ('on_chain_registered',)

class StockMovementInline(admin.TabularInline):
    model = StockMovement
    extra = 0
    readonly_fields = ('movement_type', 'quantity', 'remaining_balance', 'reference', 'created_at')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'title', 'supplier', 'category', 'unit_of_measure', 'unit_price', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'unit_of_measure', 'supplier')
    search_fields = ('sku', 'title', 'supplier__company_name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = (InventoryBatchInline,)

@admin.register(InventoryBatch)
class InventoryBatchAdmin(admin.ModelAdmin):
    list_display = (
        'batch_number', 'product', 'available_quantity', 'reserved_quantity',
        'initial_quantity', 'unit_cost', 'on_chain_registered', 'created_at'
    )
    list_filter = ('on_chain_registered', 'manufacture_date', 'expiry_date', 'product__supplier')
    search_fields = ('batch_number', 'product__sku', 'product__title', 'batch_hash', 'on_chain_tx_hash')
    readonly_fields = ('batch_hash', 'on_chain_registered', 'on_chain_tx_hash', 'on_chain_registered_at', 'created_at', 'updated_at')
    inlines = (StockMovementInline,)

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('batch', 'movement_type', 'quantity', 'remaining_balance', 'reference', 'actor', 'created_at')
    list_filter = ('movement_type', 'created_at')
    search_fields = ('batch__batch_number', 'reference', 'notes', 'actor__username')
    readonly_fields = ('created_at',)

