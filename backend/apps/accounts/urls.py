from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView,
    LoginView,
    CurrentUserView,
    SupplierProfileViewSet,
    RetailerProfileViewSet,
    SupplierDashboardView,
    RetailerDashboardView,
)

router = DefaultRouter()
router.register(r'suppliers', SupplierProfileViewSet, basename='supplier')
router.register(r'retailers', RetailerProfileViewSet, basename='retailer')

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/me/', CurrentUserView.as_view(), name='auth-me'),
    path('suppliers/dashboard/', SupplierDashboardView.as_view(), name='supplier-dashboard'),
    path('retailers/dashboard/', RetailerDashboardView.as_view(), name='retailer-dashboard'),
    path('', include(router.urls)),
]

