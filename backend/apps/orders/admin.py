from django.contrib import admin
from .models import PurchaseOrder, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'batch', 'quantity', 'unit_price', 'subtotal')
    readonly_fields = ('subtotal',)

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = (
        'po_number', 'retailer', 'supplier', 'status', 'total_amount',
        'currency', 'tracking_number', 'dispatched_at', 'delivered_at', 'created_at'
    )
    list_filter = ('status', 'currency', 'created_at', 'retailer', 'supplier')
    search_fields = (
        'po_number', 'retailer__business_name', 'supplier__company_name',
        'tracking_number', 'escrow_tx_hash', 'release_tx_hash', 'refund_tx_hash'
    )
    readonly_fields = (
        'po_number', 'escrow_tx_hash', 'release_tx_hash', 'refund_tx_hash',
        'on_chain_handover_id', 'handover_tx_hash', 'dispatched_at', 'delivered_at',
        'created_at', 'updated_at'
    )
    inlines = (OrderItemInline,)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'batch', 'quantity', 'unit_price', 'subtotal')
    list_filter = ('order__status', 'product__category')
    search_fields = ('order__po_number', 'product__title', 'product__sku', 'batch__batch_number')
    readonly_fields = ('subtotal',)

