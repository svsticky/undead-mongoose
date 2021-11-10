from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    
    # GET endpoints
    path('card', views.get_card, name='get_card'),
    path('products', views.get_products, name='get_products'),

    # POST endpoints
    path('transaction', views.create_transaction, name='create_transaction'),
    path('register', views.register_card, name='register_card'),
]
