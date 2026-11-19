import pytest
from datetime import date, timedelta
from decimal import Decimal
from rest_framework.test import APIClient
from apps.accounts.models import User, SupplierProfile
from apps.inventory.models import Product, InventoryBatch

@pytest.mark.django_db
class TestAnalytics:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='ai_supp', password='pwd')
        self.supplier = SupplierProfile.objects.create(
            user=self.user,
            company_name='AI Supply Co',
            stellar_payout_address='GAISUPPLIERWALLET000000000001'
        )
        self.product = Product.objects.create(
            supplier=self.supplier,
            sku='SKU-VACCINE-X',
            title='Temperature-Sensitive Vaccine Dose',
            unit_price=Decimal('80.00')
        )
        # Create an expiring batch
        self.batch_expiring = InventoryBatch.objects.create(
            product=self.product,
            batch_number='BATCH-VAC-CRITICAL',
            manufacture_date=date.today() - timedelta(days=60),
            expiry_date=date.today() + timedelta(days=15),
            initial_quantity=100,
            available_quantity=40
        )

    def test_demand_forecast_endpoint(self):
        res = self.client.get('/api/v1/analytics/demand-forecast/')
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 1
        item = [d for d in data if d['product_sku'] == 'SKU-VACCINE-X'][0]
        assert 'projected_weekly_demand' in item
        assert 'risk_level' in item
        assert 'recommendation' in item

    def test_expiry_risk_endpoint(self):
        res = self.client.get('/api/v1/analytics/expiry-risk/')
        assert res.status_code == 200
        data = res.json()
        batch_report = [d for d in data if d['batch_number'] == 'BATCH-VAC-CRITICAL'][0]
        assert batch_report['risk_status'] == 'CRITICAL_EXPIRY_WARNING'
        assert batch_report['days_until_expiry'] == 15

    def test_openai_tools_schema_endpoint(self):
        res = self.client.get('/api/v1/analytics/openai-tools/')
        assert res.status_code == 200
        data = res.json()
        assert 'tools' in data
        tool_names = [t['function']['name'] for t in data['tools']]
        assert 'check_inventory_stock' in tool_names
        assert 'create_purchase_order_with_escrow' in tool_names
        assert 'verify_soroban_batch_proof' in tool_names

