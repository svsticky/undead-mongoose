from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('products', views.products, name='products'),
    path('users', views.users, name='users'),
    path('users/<str:user_id>', views.users, name='user'),
    path('settings', views.settings_page, name='settings'),
    path('transactions', views.transactions, name='transactions'),

    path('product/toggle', views.toggle, name='toggle'),
    path('product/delete', views.delete, name='delete'),

    path('category/edit', views.category, name='category'),
    path('vat/edit', views.vat, name='vat'),
]
