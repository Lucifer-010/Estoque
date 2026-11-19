from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, InventoryBatchViewSet, StockMovementViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'batches', InventoryBatchViewSet, basename='batch')
router.register(r'movements', StockMovementViewSet, basename='movement')

urlpatterns = [
    path('', include(router.urls)),
]

