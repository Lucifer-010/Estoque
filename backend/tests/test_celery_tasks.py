import pytest
from datetime import date
from decimal import Decimal
from apps.accounts.models import User, SupplierProfile, RetailerProfile
from apps.inventory.models import Product, InventoryBatch
from apps.orders.models import PurchaseOrder
from apps.blockchain.tasks import (
    task_anchor_batch_proof,
    task_fund_escrow,
    task_release_escrow,
    task_refund_escrow,
)

@pytest.mark.django_db
class TestCeleryTasks:
    def setup_method(self):
        self.supp_user = User.objects.create_user(username='cel_supp', password='pwd', role=User.Role.SUPPLIER)
        self.supplier = SupplierProfile.objects.create(
            user=self.supp_user,
            company_name='Celery Hardware',
            stellar_payout_address='GCELERY00000000000000000000000000000001'
        )

        self.ret_user = User.objects.create_user(username='cel_ret', password='pwd', role=User.Role.RETAILER)
        self.retailer = RetailerProfile.objects.create(
            user=self.ret_user,
            business_name='Celery Retailer',
            stellar_wallet_address='GCELERY00000000000000000000000000000002'
        )

        self.product = Product.objects.create(
            supplier=self.supplier,
            sku='SKU-CELERY-01',
            title='Industrial Controller Box',
            unit_price=Decimal('250.00')
        )

        self.batch = InventoryBatch.objects.create(
            product=self.product,
            batch_number='BATCH-CELERY-100',
            manufacture_date=date.today(),
            initial_quantity=50,
            available_quantity=50
        )

        self.order = PurchaseOrder.objects.create(
            retailer=self.retailer,
            supplier=self.supplier,
            total_amount=Decimal('1000.00'),
            status=PurchaseOrder.Status.PENDING_ESCROW
        )

    def test_async_anchor_batch_proof(self):
        res = task_anchor_batch_proof.apply(args=[self.batch.id]).get()
        assert res['success'] is True
        self.batch.refresh_from_db()
        assert self.batch.on_chain_registered is True

    def test_async_escrow_workflow_tasks(self):
        fund_res = task_fund_escrow.apply(args=[self.order.id]).get()
        assert fund_res['success'] is True
        self.order.refresh_from_db()
        assert self.order.status == PurchaseOrder.Status.ESCROW_FUNDED

        rel_res = task_release_escrow.apply(args=[self.order.id]).get()
        assert rel_res['success'] is True
        self.order.refresh_from_db()
        assert self.order.status == PurchaseOrder.Status.COMPLETED

    def test_async_refund_task(self):
        order2 = PurchaseOrder.objects.create(
            retailer=self.retailer,
            supplier=self.supplier,
            total_amount=Decimal('500.00'),
            status=PurchaseOrder.Status.PENDING_ESCROW
        )
        task_fund_escrow.apply(args=[order2.id]).get()
        ref_res = task_refund_escrow.apply(args=[order2.id]).get()
        assert ref_res['success'] is True
        order2.refresh_from_db()
        assert order2.status == PurchaseOrder.Status.REFUNDED

