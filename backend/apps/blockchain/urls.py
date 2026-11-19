from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BlockchainTransactionRecordViewSet,
    ContractStatusView,
    EscrowLookupView,
)

router = DefaultRouter()
router.register(r'transactions', BlockchainTransactionRecordViewSet, basename='blockchain-transactions')

urlpatterns = [
    path('status/', ContractStatusView.as_view(), name='contract-status'),
    path('escrow/<int:order_id>/', EscrowLookupView.as_view(), name='escrow-lookup'),
    path('', include(router.urls)),
]

