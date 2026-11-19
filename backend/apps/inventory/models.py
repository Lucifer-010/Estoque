import hashlib
from django.db import models
from django.conf import settings
from apps.accounts.models import SupplierProfile

class Product(models.Model):
    class UnitOfMeasure(models.TextChoices):
        UNIT = 'UNIT', 'Unit / Item'
        KG = 'KG', 'Kilogram'
        BOX = 'BOX', 'Box'
        PALLET = 'PALLET', 'Pallet'
        LITER = 'LITER', 'Liter'

    supplier = models.ForeignKey(SupplierProfile, on_delete=models.CASCADE, related_name='products')
    sku = models.CharField(max_length=64, unique=True, help_text="Unique Stock Keeping Unit")
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=100, default='General')
    description = models.TextField(blank=True)
    unit_of_measure = models.CharField(max_length=20, choices=UnitOfMeasure.choices, default=UnitOfMeasure.UNIT)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Unit price in USDC")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.sku}] {self.title}"

class InventoryBatch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=100, unique=True)
    manufacture_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    initial_quantity = models.PositiveIntegerField()
    available_quantity = models.PositiveIntegerField()
    reserved_quantity = models.PositiveIntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    # Soroban on-chain anchor fields
    batch_hash = models.CharField(max_length=64, blank=True, help_text="SHA-256 hash of batch metadata for Soroban proof")
    on_chain_registered = models.BooleanField(default=False)
    on_chain_tx_hash = models.CharField(max_length=128, blank=True)
    on_chain_registered_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_hash(self) -> str:
        """Compute deterministic SHA-256 hash of batch data for Soroban registration."""
        payload = f"{self.product.sku}|{self.batch_number}|{self.manufacture_date}|{self.initial_quantity}|{self.product.supplier.stellar_payout_address}"
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    def save(self, *args, **kwargs):
        if not self.available_quantity and self.initial_quantity:
            self.available_quantity = self.initial_quantity
        if not self.batch_hash:
            self.batch_hash = self.calculate_hash()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Batch {self.batch_number} - {self.product.title} (Avail: {self.available_quantity})"

class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        INCOMING = 'INCOMING', 'Stock Arrival / Inward'
        OUTGOING = 'OUTGOING', 'Stock Removal / Sales'
        RESERVED = 'RESERVED', 'Stock Reserved for Purchase Order'
        RELEASED = 'RELEASED', 'Stock Unreserved / Cancelled PO'
        DISPATCHED = 'DISPATCHED', 'Stock Dispatched / In Transit'
        ADJUSTMENT = 'ADJUSTMENT', 'Inventory Audit Adjustment'

    batch = models.ForeignKey(InventoryBatch, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    quantity = models.IntegerField(help_text="Positive for addition, negative for reduction")
    remaining_balance = models.PositiveIntegerField(default=0)
    reference = models.CharField(max_length=100, blank=True, help_text="PO number or Audit ID")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.movement_type} ({self.quantity}) on Batch {self.batch.batch_number} at {self.created_at}"

