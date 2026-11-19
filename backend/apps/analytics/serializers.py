from rest_framework import serializers

class DemandForecastSerializer(serializers.Serializer):
    product_sku = serializers.CharField()
    product_title = serializers.CharField()
    current_available_stock = serializers.IntegerField()
    projected_weekly_demand = serializers.IntegerField()
    recommended_reorder_quantity = serializers.IntegerField()
    risk_level = serializers.CharField()
    recommendation = serializers.CharField()

class ExpiryRiskSerializer(serializers.Serializer):
    batch_number = serializers.CharField()
    product_title = serializers.CharField()
    available_quantity = serializers.IntegerField()
    expiry_date = serializers.DateField(allow_null=True)
    days_until_expiry = serializers.IntegerField(allow_null=True)
    risk_status = serializers.CharField()

