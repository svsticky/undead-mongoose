from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('products', views.products, name='products'),

    path('product/toggle', views.toggle, name='toggle'),
    path('product/delete', views.delete, name='delete'),
    path('product/edit', views.edit, name='edit'),
]
