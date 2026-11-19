import pytest
from rest_framework.test import APIClient
from apps.accounts.models import User, SupplierProfile, RetailerProfile

@pytest.mark.django_db
class TestAccounts:
    def setup_method(self):
        self.client = APIClient()

    def test_register_supplier(self):
        payload = {
            'username': 'acme_supplier',
            'email': 'acme@supplier.com',
            'password': 'Password123!',
            'role': 'SUPPLIER',
            'business_name': 'Acme Manufacturing Inc',
            'stellar_wallet_address': 'GBTESTNETSUPPLIERWALLET1234567890ABCDEF'
        }
        response = self.client.post('/api/v1/accounts/auth/register/', payload, format='json')
        assert response.status_code == 201
        data = response.json()
        assert data['username'] == 'acme_supplier'
        assert data['role'] == 'SUPPLIER'
        assert SupplierProfile.objects.filter(company_name='Acme Manufacturing Inc').exists()

    def test_register_retailer(self):
        payload = {
            'username': 'best_retailer',
            'email': 'best@retailer.com',
            'password': 'Password123!',
            'role': 'RETAILER',
            'business_name': 'Best Buy Corner Store',
            'stellar_wallet_address': 'GBTESTNETRETAILERWALLET1234567890ABCDEF'
        }
        response = self.client.post('/api/v1/accounts/auth/register/', payload, format='json')
        assert response.status_code == 201
        assert RetailerProfile.objects.filter(business_name='Best Buy Corner Store').exists()

    def test_login(self):
        user = User.objects.create_user(username='loginuser', password='SecretPassword123')
        payload = {
            'username': 'loginuser',
            'password': 'SecretPassword123'
        }
        response = self.client.post('/api/v1/accounts/auth/login/', payload, format='json')
        assert response.status_code == 200
        assert response.json()['message'] == 'Login successful'

    def test_supplier_and_retailer_dashboards(self):
        supp_user = User.objects.create_user(username='dash_supp', password='pass', role=User.Role.SUPPLIER)
        supp = SupplierProfile.objects.create(
            user=supp_user,
            company_name='Dash Supplier Co',
            contact_email='supp@dash.com',
            stellar_payout_address='GDASHSUPPLIER'
        )
        ret_user = User.objects.create_user(username='dash_ret', password='pass', role=User.Role.RETAILER)
        RetailerProfile.objects.create(
            user=ret_user,
            business_name='Dash Retailer Co',
            contact_email='ret@dash.com',
            stellar_wallet_address='GDASHRETAILER'
        )

        supp_res = self.client.get(f'/api/v1/accounts/suppliers/dashboard/?supplier_id={supp.id}')
        assert supp_res.status_code == 200
        assert supp_res.json()['role'] == 'SUPPLIER'
        assert 'metrics' in supp_res.json()

        ret_res = self.client.get('/api/v1/accounts/retailers/dashboard/')
        assert ret_res.status_code == 200
        assert ret_res.json()['role'] == 'RETAILER'
        assert 'metrics' in ret_res.json()

