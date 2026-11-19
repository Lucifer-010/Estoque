from django.urls import path
from .views import SmartDemandForecastView, ExpiryRiskView, OpenAIToolsSchemaView

urlpatterns = [
    path('demand-forecast/', SmartDemandForecastView.as_view(), name='analytics-demand-forecast'),
    path('expiry-risk/', ExpiryRiskView.as_view(), name='analytics-expiry-risk'),
    path('openai-tools/', OpenAIToolsSchemaView.as_view(), name='analytics-openai-tools'),
]

