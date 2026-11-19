from datetime import date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from drf_spectacular.utils import extend_schema, OpenApiResponse
from apps.inventory.models import Product, InventoryBatch
from apps.orders.models import PurchaseOrder
from .serializers import DemandForecastSerializer, ExpiryRiskSerializer

class SmartDemandForecastView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['Analytics & AI Insights'],
        summary='AI-assisted smart demand forecast and automated reorder recommendations',
        responses={200: DemandForecastSerializer(many=True)}
    )
    def get(self, request):
        products = Product.objects.all().prefetch_related('batches')
        forecasts = []

        for p in products:
            avail = sum(b.available_quantity for b in p.batches.all())
            # Estimate simulated weekly velocity based on historical orders
            recent_orders = PurchaseOrder.objects.filter(items__product=p, status__in=['COMPLETED', 'DISPATCHED'])
            velocity = sum(i.quantity for o in recent_orders for i in o.items.filter(product=p))
            weekly_demand = max(10, int(velocity * 1.25))

            if avail < weekly_demand:
                risk = "HIGH_STOCKOUT_RISK"
                reorder = (weekly_demand * 4) - avail
                rec = f"Urgent: Stock ({avail}) is below weekly demand ({weekly_demand}). Recommend reordering {reorder} units immediately."
            elif avail < weekly_demand * 2:
                risk = "MEDIUM_RISK"
                reorder = (weekly_demand * 3) - avail
                rec = f"Stock level is moderate. Plan reorder of {reorder} units within 14 days."
            else:
                risk = "HEALTHY"
                reorder = 0
                rec = f"Inventory healthy. Available buffer for {avail // max(1, weekly_demand)} weeks."

            forecasts.append({
                'product_sku': p.sku,
                'product_title': p.title,
                'current_available_stock': avail,
                'projected_weekly_demand': weekly_demand,
                'recommended_reorder_quantity': max(0, reorder),
                'risk_level': risk,
                'recommendation': rec
            })

        return Response(forecasts)

class ExpiryRiskView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['Analytics & AI Insights'],
        summary='Perishable inventory batch expiry risk monitoring',
        responses={200: ExpiryRiskSerializer(many=True)}
    )
    def get(self, request):
        today = date.today()
        batches = InventoryBatch.objects.filter(available_quantity__gt=0).select_related('product')
        results = []

        for b in batches:
            if b.expiry_date:
                days_left = (b.expiry_date - today).days
                if days_left < 0:
                    status_risk = "EXPIRED"
                elif days_left <= 30:
                    status_risk = "CRITICAL_EXPIRY_WARNING"
                elif days_left <= 90:
                    status_risk = "ATTENTION_REQUIRED"
                else:
                    status_risk = "NORMAL"
            else:
                days_left = None
                status_risk = "NON_PERISHABLE"

            results.append({
                'batch_number': b.batch_number,
                'product_title': b.product.title,
                'available_quantity': b.available_quantity,
                'expiry_date': b.expiry_date,
                'days_until_expiry': days_left,
                'risk_status': status_risk
            })

        return Response(results)

class OpenAIToolsSchemaView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['Analytics & AI Insights'],
        summary='OpenAI Function Calling Tool definitions for AI agent automation',
        responses={200: OpenApiResponse(description="OpenAI function calling schemas")}
    )
    def get(self, request):
        """Returns OpenAI-compatible tools schema for autonomous agent execution."""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "check_inventory_stock",
                    "description": "Check current available stock, batches, and proofs for a product SKU",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sku": {"type": "string", "description": "Stock Keeping Unit"}
                        },
                        "required": ["sku"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_purchase_order_with_escrow",
                    "description": "Create a purchase order and fund it via Soroban USDC escrow",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "retailer_id": {"type": "integer"},
                            "supplier_id": {"type": "integer"},
                            "product_id": {"type": "integer"},
                            "quantity": {"type": "integer"}
                        },
                        "required": ["retailer_id", "supplier_id", "product_id", "quantity"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "verify_soroban_batch_proof",
                    "description": "Verify on-chain SHA-256 batch proof registered on Stellar Testnet Soroban contract",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "batch_id": {"type": "integer"}
                        },
                        "required": ["batch_id"]
                    }
                }
            }
        ]
        return Response({"tools": tools})

