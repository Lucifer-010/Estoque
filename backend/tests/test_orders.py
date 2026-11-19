import pytest
from datetime import date
from decimal import Decimal
from rest_framework.test import APIClient
from apps.accounts.models import User, SupplierProfile, RetailerProfile
from apps.inventory.models import Product, InventoryBatch
from apps.orders.models import PurchaseOrder

@pytest.mark.django_db
class TestOrdersAndEscrow:
    def setup_method(self):
        self.client = APIClient()

        # Supplier
        self.supp_user = User.objects.create_user(username='ord_supp', password='pwd', role=User.Role.SUPPLIER)
        self.supplier = SupplierProfile.objects.create(
            user=self.supp_user,
            company_name='Global Supplies Ltd',
            contact_email='supp@global.com',
            stellar_payout_address='GSUPPLIERPAYOUTWALLET123456789'
        )

        # Retailer
        self.ret_user = User.objects.create_user(username='ord_ret', password='pwd', role=User.Role.RETAILER)
        self.retailer = RetailerProfile.objects.create(
            user=self.ret_user,
            business_name='Metropolis Mart',
            contact_email='ret@metropolis.com',
            stellar_wallet_address='GRETAILERPAYMENTWALLET987654321'
        )

        # Product & Batch
        self.product = Product.objects.create(
            supplier=self.supplier,
            sku='SKU-ROUTER-5G',
            title='Industrial 5G Gateway Router',
            unit_price=Decimal('500.00')
        )
        self.batch = InventoryBatch.objects.create(
            product=self.product,
            batch_number='BATCH-ROUTER-001',
            manufacture_date=date.today(),
            initial_quantity=100,
            available_quantity=100
        )

    def test_create_purchase_order_and_inventory_reservation(self):
        payload = {
            'retailer': self.retailer.id,
            'supplier': self.supplier.id,
            'items': [
                {
                    'product': self.product.id,
                    'batch': self.batch.id,
                    'quantity': 20,
                    'unit_price': '500.00'
                }
            ]
        }
        res = self.client.post('/api/v1/orders/', payload, format='json')
        assert res.status_code == 201
        data = res.json()
        assert data['status'] == PurchaseOrder.Status.PENDING_ESCROW
        assert Decimal(data['total_amount']) == Decimal('10000.00')

        # Check stock was reserved
        self.batch.refresh_from_db()
        assert self.batch.available_quantity == 80
        assert self.batch.reserved_quantity == 20

    def test_full_successful_escrow_and_delivery_lifecycle(self):
        # 1. Create PO
        payload = {
            'retailer': self.retailer.id,
            'supplier': self.supplier.id,
            'items': [
                {
                    'product': self.product.id,
                    'batch': self.batch.id,
                    'quantity': 10,
                    'unit_price': '500.00'
                }
            ]
        }
        create_res = self.client.post('/api/v1/orders/', payload, format='json')
        order_id = create_res.json()['id']

        # 2. Fund Escrow (USDC locked on Soroban)
        fund_res = self.client.post(f'/api/v1/orders/{order_id}/fund-escrow/')
        assert fund_res.status_code == 200
        assert fund_res.json()['status'] == 'ESCROW_FUNDED'

        po = PurchaseOrder.objects.get(id=order_id)
        assert po.status == PurchaseOrder.Status.ESCROW_FUNDED
        assert len(po.escrow_tx_hash) == 64

        # Cannot fund twice
        dup_fund_res = self.client.post(f'/api/v1/orders/{order_id}/fund-escrow/')
        assert dup_fund_res.status_code == 400

        # 3. Dispatch order
        dispatch_res = self.client.post(f'/api/v1/orders/{order_id}/dispatch/', {
            'tracking_number': 'TRK-98234-EXP',
            'shipping_carrier': 'FedEx International'
        }, format='json')
        assert dispatch_res.status_code == 200
        po.refresh_from_db()
        assert po.status == PurchaseOrder.Status.DISPATCHED
        assert po.tracking_number == 'TRK-98234-EXP'
        assert po.on_chain_handover_id is not None

        # 4. Confirm receipt -> releases payment to supplier
        receipt_res = self.client.post(f'/api/v1/orders/{order_id}/confirm-receipt/', {
            'delivery_notes': 'All 10 units received in perfect condition.'
        }, format='json')
        assert receipt_res.status_code == 200
        po.refresh_from_db()
        assert po.status == PurchaseOrder.Status.COMPLETED
        assert len(po.release_tx_hash) == 64

        # 5. Prevent duplicate settlement (duplicate release rejected)
        dup_receipt_res = self.client.post(f'/api/v1/orders/{order_id}/confirm-receipt/', {
            'delivery_notes': 'Second attempt'
        }, format='json')
        assert dup_receipt_res.status_code == 400

    def test_pre_dispatch_cancellation_and_escrow_refund(self):
        # Create PO
        create_res = self.client.post('/api/v1/orders/', {
            'retailer': self.retailer.id,
            'supplier': self.supplier.id,
            'items': [{'product': self.product.id, 'batch': self.batch.id, 'quantity': 15}]
        }, format='json')
        order_id = create_res.json()['id']

        # Fund escrow
        self.client.post(f'/api/v1/orders/{order_id}/fund-escrow/')
        po = PurchaseOrder.objects.get(id=order_id)
        assert po.status == PurchaseOrder.Status.ESCROW_FUNDED

        # Cancel and refund before dispatch
        cancel_res = self.client.post(f'/api/v1/orders/{order_id}/cancel-refund/')
        assert cancel_res.status_code == 200
        po.refresh_from_db()
        assert po.status == PurchaseOrder.Status.REFUNDED
        assert len(po.refund_tx_hash) == 64

        # Inventory released back
        self.batch.refresh_from_db()
        assert self.batch.available_quantity == 100
        assert self.batch.reserved_quantity == 0

        # Cannot cancel again
        bad_cancel = self.client.post(f'/api/v1/orders/{order_id}/cancel-refund/')
        assert bad_cancel.status_code == 400

