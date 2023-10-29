from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    
    # GET endpoints
    path('card', views.get_card, name='get_card'),
    path('products', views.get_products, name='get_products'),
    path('confirm', views.confirm_card, name='confirm_card'),
    path('product_transactions', views.get_product_transactions, name="get_product_transactions"),

    # POST endpoints
    path('transaction', views.create_transaction, name='create_transaction'),
    path('register', views.register_card, name='register_card'),
    path('catchwebhook', views.on_webhook, name='receive_update')
]
