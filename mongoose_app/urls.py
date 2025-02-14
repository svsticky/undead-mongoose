from django.urls import path
from django.conf import settings
from . import views
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Define schema view for drf-yasg (only if DEBUG is True)
schema_view = None
if settings.DEBUG:
    schema_view = get_schema_view(
        openapi.Info(
            title="Mongoose API",
            default_version='v1',
            description="API Documentation for the Mongoose POS",
            contact=openapi.Contact(email="mongoose@svsticky.nl"),
            license=openapi.License(name="MIT License"),
        ),
        public=True,
        permission_classes=(permissions.AllowAny,),
    )

urlpatterns = [
    # Your API endpoints here
    path("card", views.GetCard.as_view(), name="get_card"),
    path("products", views.GetProducts.as_view(), name="get_products"),
    path("confirm", views.ConfirmCard.as_view(), name="confirm_card"),
    path("transaction", views.CreateTransaction.as_view(), name="create_transaction"),
    path("balance", views.UpdateBalance.as_view(), name="update_balance"),
    path("register", views.RegisterCard.as_view(), name="register_card"),
    path("catchwebhook", views.WebhookReceiver.as_view(), name="receive_update"),
    path("topup", views.TopUp.as_view(), name="topup"),
    path("payment/webhook", views.PaymentWebhook.as_view(), name="payment_webhook"),

    # Only include Swagger and ReDoc paths if schema_view is defined (i.e., DEBUG=True)
    *(
        [
            path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-ui'),
            path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='redoc-ui')
        ]
        if schema_view
        else []
    )
]
