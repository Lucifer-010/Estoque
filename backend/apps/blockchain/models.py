from django.db import models
from apps.orders.models import PurchaseOrder
from apps.inventory.models import InventoryBatch

class BlockchainTransactionRecord(models.Model):
    class TxType(models.TextChoices):
        BATCH_PROOF = 'BATCH_PROOF', 'Inventory Batch Proof Anchoring'
        ESCROW_FUND = 'ESCROW_FUND', 'Soroban Escrow USDC Locked'
        ESCROW_RELEASE = 'ESCROW_RELEASE', 'Soroban Escrow Released to Supplier'
        ESCROW_REFUND = 'ESCROW_REFUND', 'Soroban Escrow Refunded to Retailer'
        HANDOVER_RECORD = 'HANDOVER_RECORD', 'Custody Handover Dispatched'
        CUSTODY_ACK = 'CUSTODY_ACK', 'Retailer Custody Acknowledged'

    class Status(models.TextChoices):
        SUCCESS = 'SUCCESS', 'Confirmed on Stellar Testnet'
        PENDING = 'PENDING', 'Submitted / In Mempool'
        FAILED = 'FAILED', 'Failed / Rejected'

    tx_type = models.CharField(max_length=30, choices=TxType.choices)
    order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='blockchain_records')
    batch = models.ForeignKey(InventoryBatch, on_delete=models.SET_NULL, null=True, blank=True, related_name='blockchain_records')
    contract_id = models.CharField(max_length=128)
    tx_hash = models.CharField(max_length=128, unique=True)
    sender_address = models.CharField(max_length=64, blank=True)
    recipient_address = models.CharField(max_length=64, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUCCESS)
    ledger_sequence = models.BigIntegerField(default=1054321)
    raw_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.tx_type}] {self.tx_hash[:16]}... ({self.status})"

