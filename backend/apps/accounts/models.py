from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        SUPPLIER = 'SUPPLIER', 'Supplier'
        RETAILER = 'RETAILER', 'Retailer'
        ADMIN = 'ADMIN', 'Administrator'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.RETAILER,
        help_text="Role determining permissions and accessible dashboard"
    )
    stellar_wallet_address = models.CharField(
        max_length=64,
        blank=True,
        help_text="Public Stellar Testnet address (e.g. G...)"
    )

    def is_supplier(self):
        return self.role == self.Role.SUPPLIER

    def is_retailer(self):
        return self.role == self.Role.RETAILER

class SupplierProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='supplier_profile')
    company_name = models.CharField(max_length=255)
    business_registration_number = models.CharField(max_length=100, blank=True)
    contact_email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    stellar_payout_address = models.CharField(
        max_length=64,
        help_text="Stellar address where escrow payments will be released"
    )
    is_verified = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company_name} ({self.user.username})"

class RetailerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='retailer_profile')
    business_name = models.CharField(max_length=255)
    tax_id = models.CharField(max_length=100, blank=True)
    contact_email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    delivery_address = models.TextField(blank=True)
    stellar_wallet_address = models.CharField(
        max_length=64,
        help_text="Stellar address used to fund purchase order escrows"
    )
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=100000.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.business_name} ({self.user.username})"

