from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

def api_root(request):
    return JsonResponse({
        'name': 'Estoque Supply Chain & Soroban Escrow API',
        'version': '1.0.0',
        'documentation': {
            'swagger_ui': '/api/docs/',
            'redoc': '/api/redoc/',
            'openapi_schema': '/api/schema/',
        },
        'endpoints': {
            'accounts_and_auth': '/api/v1/accounts/',
            'inventory_and_batches': '/api/v1/inventory/',
            'purchase_orders': '/api/v1/orders/',
            'blockchain_and_soroban': '/api/v1/blockchain/',
            'analytics_and_ai': '/api/v1/analytics/',
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', api_root, name='api-root'),

    # OpenAPI 3.0 / Swagger Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API v1 routes
    path('api/v1/accounts/', include('apps.accounts.urls')),
    path('api/v1/inventory/', include('apps.inventory.urls')),
    path('api/v1/orders/', include('apps.orders.urls')),
    path('api/v1/blockchain/', include('apps.blockchain.urls')),
    path('api/v1/analytics/', include('apps.analytics.urls')),
]

