from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, SupplierProfile, RetailerProfile

class SupplierProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = SupplierProfile
        fields = [
            'id', 'user', 'username', 'company_name', 'business_registration_number',
            'contact_email', 'phone', 'address', 'stellar_payout_address',
            'is_verified', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class RetailerProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = RetailerProfile
        fields = [
            'id', 'user', 'username', 'business_name', 'tax_id',
            'contact_email', 'phone', 'delivery_address',
            'stellar_wallet_address', 'credit_limit', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class UserSerializer(serializers.ModelSerializer):
    supplier_profile = SupplierProfileSerializer(read_only=True)
    retailer_profile = RetailerProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'stellar_wallet_address', 'supplier_profile', 'retailer_profile'
        ]
        read_only_fields = ['id']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=6)
    business_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    stellar_wallet_address = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role', 'stellar_wallet_address', 'business_name']

    def create(self, validated_data):
        business_name = validated_data.pop('business_name', '') or validated_data.get('username')
        password = validated_data.pop('password')
        stellar_address = validated_data.get('stellar_wallet_address') or 'GBTESTNETDEFAULTWALLETADDRESS1234567890ABCDEF'
        validated_data['stellar_wallet_address'] = stellar_address

        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        if user.role == User.Role.SUPPLIER:
            SupplierProfile.objects.create(
                user=user,
                company_name=business_name,
                contact_email=user.email or f"{user.username}@supplier.estoque.com",
                stellar_payout_address=stellar_address
            )
        elif user.role == User.Role.RETAILER:
            RetailerProfile.objects.create(
                user=user,
                business_name=business_name,
                contact_email=user.email or f"{user.username}@retailer.estoque.com",
                stellar_wallet_address=stellar_address
            )

        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs.get('username'), password=attrs.get('password'))
        if not user:
            raise serializers.ValidationError("Invalid username or password.")
        attrs['user'] = user
        return attrs

