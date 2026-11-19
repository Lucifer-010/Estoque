from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, SupplierProfile, RetailerProfile

class SupplierProfileInline(admin.StackedInline):
    model = SupplierProfile
    can_delete = False
    verbose_name_plural = 'Supplier Profile'
    extra = 0

class RetailerProfileInline(admin.StackedInline):
    model = RetailerProfile
    can_delete = False
    verbose_name_plural = 'Retailer Profile'
    extra = 0

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'stellar_wallet_address', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'stellar_wallet_address')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Estoque Domain Role & Stellar Wallet', {'fields': ('role', 'stellar_wallet_address')}),
    )
    inlines = (SupplierProfileInline, RetailerProfileInline)

@admin.register(SupplierProfile)
class SupplierProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'contact_email', 'stellar_payout_address', 'is_verified', 'created_at')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('company_name', 'user__username', 'contact_email', 'stellar_payout_address')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(RetailerProfile)
class RetailerProfileAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'user', 'contact_email', 'stellar_wallet_address', 'credit_limit', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('business_name', 'user__username', 'contact_email', 'stellar_wallet_address')
    readonly_fields = ('created_at', 'updated_at')

