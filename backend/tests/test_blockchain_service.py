import pytest
from datetime import date
from decimal import Decimal
from apps.accounts.models import User, SupplierProfile, RetailerProfile
from apps.inventory.models import Product, InventoryBatch
from apps.orders.models import PurchaseOrder
from apps.blockchain.services import BlockchainService
from apps.blockchain.models import BlockchainTransactionRecord

@pytest.mark.django_db
class TestBlockchainService:
    def setup_method(self):
        self.service = BlockchainService()

        self.supp_user = User.objects.create_user(username='bc_supp', password='pwd', role=User.Role.SUPPLIER)
        self.supplier = SupplierProfile.objects.create(
            user=self.supp_user,
            company_name='Stellar Chain Suppliers',
            stellar_payout_address='GBCHAIN0000000000000000000000000000000001'
        )

        self.ret_user = User.objects.create_user(username='bc_ret', password='pwd', role=User.Role.RETAILER)
        self.retailer = RetailerProfile.objects.create(
            user=self.ret_user,
            business_name='Stellar Chain Retailers',
            stellar_wallet_address='GBCHAIN0000000000000000000000000000000002'
        )

        self.product = Product.objects.create(
            supplier=self.supplier,
            sku='SKU-BC-001',
            title='Smart Meter Sensor',
            unit_price=Decimal('150.00')
        )

        self.batch = InventoryBatch.objects.create(
            product=self.product,
            batch_number='BATCH-BC-101',
            manufacture_date=date.today(),
            initial_quantity=200,
            available_quantity=200
        )

        self.order = PurchaseOrder.objects.create(
            retailer=self.retailer,
            supplier=self.supplier,
            total_amount=Decimal('3000.00'),
            status=PurchaseOrder.Status.PENDING_ESCROW
        )

    def test_register_batch_proof(self):
        res = self.service.register_batch_proof(self.batch)
        assert res['success'] is True
        assert len(res['tx_hash']) == 64
        assert BlockchainTransactionRecord.objects.filter(tx_hash=res['tx_hash']).exists()

    def test_escrow_fund_and_duplicate_release_prevention(self):
        fund_res = self.service.fund_escrow(self.order)
        assert fund_res['success'] is True
        assert self.order.status == PurchaseOrder.Status.ESCROW_FUNDED

        rel_res = self.service.release_escrow(self.order)
        assert rel_res['success'] is True
        assert self.order.status == PurchaseOrder.Status.COMPLETED

        # Duplicate release attempt must raise ValueError
        with pytest.raises(ValueError) as exc:
            self.service.release_escrow(self.order)
        assert "Duplicate settlement prevented" in str(exc.value)

    def test_escrow_fund_and_duplicate_refund_prevention(self):
        order2 = PurchaseOrder.objects.create(
            retailer=self.retailer,
            supplier=self.supplier,
            total_amount=Decimal('1500.00'),
            status=PurchaseOrder.Status.PENDING_ESCROW
        )
        self.service.fund_escrow(order2)
        ref_res = self.service.refund_escrow(order2)
        assert ref_res['success'] is True

        # Duplicate refund attempt must raise ValueError
        with pytest.raises(ValueError) as exc:
            self.service.refund_escrow(order2)
        assert "Duplicate settlement prevented" in str(exc.value)

    def test_handover_and_custody_acknowledgment(self):
        handover_res = self.service.record_handover(self.order)
        assert handover_res['success'] is True
        assert 'handover_id' in handover_res

        ack_res = self.service.acknowledge_custody(self.order)
        assert ack_res['success'] is True
        assert ack_res['status'] == 'CUSTODY_ACKNOWLEDGED'

