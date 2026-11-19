import pytest
from datetime import date
from decimal import Decimal
from rest_framework.test import APIClient
from apps.accounts.models import User, SupplierProfile
from apps.inventory.models import Product, InventoryBatch, StockMovement

@pytest.mark.django_db
class TestInventory:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='inv_supplier', password='password', role=User.Role.SUPPLIER)
        self.supplier = SupplierProfile.objects.create(
            user=self.user,
            company_name='Nova Tech Supplies',
            contact_email='contact@novatech.com',
            stellar_payout_address='GNOVA1234567890ABCDEF'
        )

    def test_product_registration_and_sku(self):
        payload = {
            'supplier': self.supplier.id,
            'sku': 'SKU-DRONE-4K',
            'title': 'Industrial Surveillance Drone 4K',
            'category': 'Electronics',
            'description': 'High precision thermal imaging drone',
            'unit_of_measure': 'UNIT',
            'unit_price': '1250.00'
        }
        response = self.client.post('/api/v1/inventory/products/', payload, format='json')
        assert response.status_code == 201
        data = response.json()
        assert data['sku'] == 'SKU-DRONE-4K'
        assert data['total_stock'] == 0

    def test_batch_creation_hash_and_movements(self):
        product = Product.objects.create(
            supplier=self.supplier,
            sku='SKU-SOLAR-500W',
            title='Monocrystalline Solar Panel 500W',
            unit_price=Decimal('180.00')
        )
        payload = {
            'product': product.id,
            'batch_number': 'BATCH-2026-SOLAR-01',
            'manufacture_date': '2026-05-10',
            'expiry_date': '2036-05-10',
            'initial_quantity': 500,
            'available_quantity': 500,
            'unit_cost': '120.00'
        }
        response = self.client.post('/api/v1/inventory/batches/', payload, format='json')
        assert response.status_code == 201
        batch_id = response.json()['id']

        batch = InventoryBatch.objects.get(id=batch_id)
        assert len(batch.batch_hash) == 64
        # Movement audit log created
        assert StockMovement.objects.filter(batch=batch, movement_type=StockMovement.MovementType.INCOMING).exists()

    def test_stock_adjustment(self):
        product = Product.objects.create(
            supplier=self.supplier,
            sku='SKU-BATTERY-LFP',
            title='10kWh LFP Storage Battery',
            unit_price=Decimal('2500.00')
        )
        batch = InventoryBatch.objects.create(
            product=product,
            batch_number='BATCH-BATTERY-99',
            manufacture_date=date.today(),
            initial_quantity=50,
            available_quantity=50
        )

        # Subtract 10 units via audit adjustment
        res = self.client.post(f'/api/v1/inventory/batches/{batch.id}/adjust-stock/', {
            'quantity_change': -10,
            'reason': 'Damaged during warehouse transit'
        }, format='json')
        assert res.status_code == 200
        batch.refresh_from_db()
        assert batch.available_quantity == 40

        # Attempt to subtract more than available
        bad_res = self.client.post(f'/api/v1/inventory/batches/{batch.id}/adjust-stock/', {
            'quantity_change': -50,
            'reason': 'Excessive deduction'
        }, format='json')
        assert bad_res.status_code == 400

    def test_register_on_chain_batch_proof(self):
        product = Product.objects.create(
            supplier=self.supplier,
            sku='SKU-CHIP-AI',
            title='Edge AI Accelerator Chip',
            unit_price=Decimal('45.00')
        )
        batch = InventoryBatch.objects.create(
            product=product,
            batch_number='BATCH-CHIP-777',
            manufacture_date=date.today(),
            initial_quantity=1000,
            available_quantity=1000
        )

        res = self.client.post(f'/api/v1/inventory/batches/{batch.id}/register-proof/')
        assert res.status_code == 200
        data = res.json()
        assert data['success'] is True
        assert len(data['tx_hash']) == 64
        batch.refresh_from_db()
        assert batch.on_chain_registered is True
        assert batch.on_chain_tx_hash == data['tx_hash']

