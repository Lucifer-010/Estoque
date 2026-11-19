import uuid
from decimal import Decimal
from django.db import models
from apps.accounts.models import SupplierProfile, RetailerProfile
from apps.inventory.models import Product, InventoryBatch, StockMovement

class PurchaseOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        PENDING_ESCROW = 'PENDING_ESCROW', 'Pending Escrow Funding'
        ESCROW_FUNDED = 'ESCROW_FUNDED', 'Escrow Funded (USDC Locked)'
        DISPATCHED = 'DISPATCHED', 'Dispatched / In Transit'
        DELIVERED = 'DELIVERED', 'Delivered to Retailer'
        COMPLETED = 'COMPLETED', 'Completed & Payment Released'
        CANCELLED = 'CANCELLED', 'Cancelled'
        REFUNDED = 'REFUNDED', 'Escrow Refunded to Retailer'

    po_number = models.CharField(max_length=64, unique=True, help_text="e.g. PO-2026-0001")
    retailer = models.ForeignKey(RetailerProfile, on_delete=models.CASCADE, related_name='purchase_orders')
    supplier = models.ForeignKey(SupplierProfile, on_delete=models.CASCADE, related_name='sales_orders')
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING_ESCROW)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=10, default="USDC")

    # On-chain Soroban references
    escrow_tx_hash = models.CharField(max_length=128, blank=True)
    release_tx_hash = models.CharField(max_length=128, blank=True)
    refund_tx_hash = models.CharField(max_length=128, blank=True)
    on_chain_handover_id = models.BigIntegerField(null=True, blank=True)
    handover_tx_hash = models.CharField(max_length=128, blank=True)

    # Logistics & Dispatch
    tracking_number = models.CharField(max_length=100, blank=True)
    shipping_carrier = models.CharField(max_length=100, blank=True, default='DHL Express')
    dispatched_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    delivery_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.po_number:
            self.po_number = f"PO-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def recalculate_total(self):
        total = sum(item.subtotal for item in self.items.all())
        self.total_amount = total
        self.save(update_fields=['total_amount', 'updated_at'])

    def __str__(self):
        return f"{self.po_number} - {self.retailer.business_name} -> {self.supplier.company_name} ({self.status})"

class OrderItem(models.Model):
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    batch = models.ForeignKey(InventoryBatch, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    def save(self, *args, **kwargs):
        if not self.unit_price:
            self.unit_price = self.product.unit_price
        self.subtotal = Decimal(str(self.quantity)) * Decimal(str(self.unit_price))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity}x {self.product.title} on {self.order.po_number}"

