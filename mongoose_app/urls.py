from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    
    # GET endpoints
    path('card', views.get_card, name='get_card'),
    path('products', views.get_products, name='get_products'),
    path('confirm', views.confirm_card, name='confirm_card'),

    # POST endpoints
    path('transaction', views.create_transaction, name='create_transaction'),
    path('balance', views.update_balance, name='update_balance'),
    path('register', views.register_card, name='register_card'),
    path('catchwebhook', views.on_webhook, name='receive_update')
]
