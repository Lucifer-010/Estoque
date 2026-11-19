from rest_framework import serializers
from .models import BlockchainTransactionRecord

class BlockchainTransactionRecordSerializer(serializers.ModelSerializer):
    order_po = serializers.CharField(source='order.po_number', read_only=True)
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True)

    class Meta:
        model = BlockchainTransactionRecord
        fields = [
            'id', 'tx_type', 'order', 'order_po', 'batch', 'batch_number',
            'contract_id', 'tx_hash', 'sender_address', 'recipient_address',
            'amount', 'status', 'ledger_sequence', 'raw_data', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class ContractStatusSerializer(serializers.Serializer):
    network = serializers.CharField()
    contract_id = serializers.CharField()
    usdc_token_contract = serializers.CharField()
    soroban_rpc = serializers.CharField()
    horizon_url = serializers.CharField()
    simulation_mode = serializers.BooleanField()
    contract_status = serializers.CharField()
    verified_methods = serializers.ListField(child=serializers.CharField())

