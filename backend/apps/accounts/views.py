from rest_framework import status, viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import login
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .models import User, SupplierProfile, RetailerProfile
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    SupplierProfileSerializer,
    RetailerProfileSerializer,
)

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['Authentication & Accounts'],
        summary='Register a new supplier or retailer account',
        request=RegisterSerializer,
        responses={201: UserSerializer}
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['Authentication & Accounts'],
        summary='Log into Estoque account',
        request=LoginSerializer,
        responses={200: UserSerializer, 400: OpenApiResponse(description="Invalid credentials")}
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            return Response({
                'message': 'Login successful',
                'user': UserSerializer(user).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CurrentUserView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['Authentication & Accounts'],
        summary='Get current user profile and role details',
        responses={200: UserSerializer}
    )
    def get(self, request):
        if request.user.is_authenticated:
            return Response(UserSerializer(request.user).data)
        # Fallback for demonstration / testing
        first_user = User.objects.first()
        if first_user:
            return Response(UserSerializer(first_user).data)
        return Response({'detail': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

class SupplierProfileViewSet(viewsets.ModelViewSet):
    queryset = SupplierProfile.objects.all().select_related('user')
    serializer_class = SupplierProfileSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(tags=['Authentication & Accounts'], summary='List or manage supplier business profiles')
    def get_queryset(self):
        return super().get_queryset()

class RetailerProfileViewSet(viewsets.ModelViewSet):
    queryset = RetailerProfile.objects.all().select_related('user')
    serializer_class = RetailerProfileSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(tags=['Authentication & Accounts'], summary='List or manage retailer business profiles')
    def get_queryset(self):
        return super().get_queryset()

class SupplierDashboardView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['Authentication & Accounts'],
        summary='Supplier Dashboard overview (Inventory, Orders, Escrow revenue)',
        responses={200: OpenApiResponse(description="Supplier dashboard metrics")}
    )
    def get(self, request):
        from apps.inventory.models import Product, InventoryBatch
        from apps.orders.models import PurchaseOrder

        supplier = SupplierProfile.objects.first()
        supplier_id = request.query_params.get('supplier_id')
        if supplier_id:
            supplier = SupplierProfile.objects.filter(id=supplier_id).first()

        products_count = Product.objects.filter(supplier=supplier).count() if supplier else Product.objects.count()
        batches = InventoryBatch.objects.filter(product__supplier=supplier) if supplier else InventoryBatch.objects.all()
        orders = PurchaseOrder.objects.filter(supplier=supplier) if supplier else PurchaseOrder.objects.all()

        total_batches = batches.count()
        on_chain_batches = batches.filter(on_chain_registered=True).count()
        total_orders = orders.count()
        pending_escrow = orders.filter(status='PENDING_ESCROW').count()
        funded_escrow = orders.filter(status='ESCROW_FUNDED').count()
        completed = orders.filter(status='COMPLETED').count()

        return Response({
            'role': 'SUPPLIER',
            'supplier_name': supplier.company_name if supplier else 'All Suppliers',
            'stellar_payout_address': supplier.stellar_payout_address if supplier else None,
            'metrics': {
                'total_products': products_count,
                'total_batches': total_batches,
                'on_chain_verified_batches': on_chain_batches,
                'total_orders': total_orders,
                'pending_escrow_orders': pending_escrow,
                'escrow_funded_orders': funded_escrow,
                'completed_orders': completed,
            }
        })

class RetailerDashboardView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['Authentication & Accounts'],
        summary='Retailer Dashboard overview (Active purchase orders, Escrow locked, Deliveries)',
        responses={200: OpenApiResponse(description="Retailer dashboard metrics")}
    )
    def get(self, request):
        from apps.orders.models import PurchaseOrder

        retailer = RetailerProfile.objects.first()
        retailer_id = request.query_params.get('retailer_id')
        if retailer_id:
            retailer = RetailerProfile.objects.filter(id=retailer_id).first()

        orders = PurchaseOrder.objects.filter(retailer=retailer) if retailer else PurchaseOrder.objects.all()

        return Response({
            'role': 'RETAILER',
            'retailer_name': retailer.business_name if retailer else 'All Retailers',
            'stellar_wallet_address': retailer.stellar_wallet_address if retailer else None,
            'metrics': {
                'total_orders': orders.count(),
                'awaiting_funding': orders.filter(status='PENDING_ESCROW').count(),
                'in_escrow_locked': orders.filter(status='ESCROW_FUNDED').count(),
                'dispatched_in_transit': orders.filter(status='DISPATCHED').count(),
                'delivered_awaiting_confirm': orders.filter(status='DELIVERED').count(),
                'completed_settled': orders.filter(status='COMPLETED').count(),
                'cancelled_or_refunded': orders.filter(status__in=['CANCELLED', 'REFUNDED']).count(),
            }
        })

