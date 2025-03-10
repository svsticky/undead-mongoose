from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.login, name='login'),

    path('products', views.products, name='products'),
    path('users', views.users, name='users'),
    path('users/<str:user_id>', views.users, name='user'),
    path('settings', views.settings_page, name='settings'),
    path('transactions', views.transactions, name='transactions'),
    path('salesInfo', views.salesInfo, name='salesInfo'),

    path('product/toggle', views.toggle, name='toggle'),
    path('product/delete', views.delete, name='delete'),

    path('category/edit', views.category, name='category'),
    path('vat/edit', views.vat, name='vat'),
    path('settings/edit', views.settings_update, name='settings_update'),

    path('transactions/export', views.export_sale_transactions, name='export_sale_transactions'),
]
