from django.contrib import admin
from .models import BlockchainTransactionRecord

@admin.register(BlockchainTransactionRecord)
class BlockchainTransactionRecordAdmin(admin.ModelAdmin):
    list_display = (
        'tx_type', 'tx_hash_short', 'order', 'batch', 'status',
        'amount', 'sender_address_short', 'recipient_address_short', 'created_at'
    )
    list_filter = ('tx_type', 'status', 'created_at')
    search_fields = (
        'tx_hash', 'contract_id', 'sender_address', 'recipient_address',
        'order__po_number', 'batch__batch_number'
    )
    readonly_fields = (
        'tx_type', 'order', 'batch', 'contract_id', 'tx_hash',
        'sender_address', 'recipient_address', 'amount', 'status',
        'ledger_sequence', 'raw_data', 'created_at'
    )

    def tx_hash_short(self, obj):
        return f"{obj.tx_hash[:12]}...{obj.tx_hash[-6:]}" if obj.tx_hash else "-"
    tx_hash_short.short_description = "Tx Hash"

    def sender_address_short(self, obj):
        return f"{obj.sender_address[:8]}...{obj.sender_address[-4:]}" if obj.sender_address else "-"
    sender_address_short.short_description = "Sender"

    def recipient_address_short(self, obj):
        return f"{obj.recipient_address[:8]}...{obj.recipient_address[-4:]}" if obj.recipient_address else "-"
    recipient_address_short.short_description = "Recipient"

