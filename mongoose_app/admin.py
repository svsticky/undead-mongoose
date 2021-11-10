from django.contrib import admin
from django.http.request import HttpRequest
from .models import Product, Category, Transaction

# Register your models here.
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'euro', 'category', 'image_view')
    readonly_fields = ['image_view']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    fields = ['name']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    
    def has_add_permission(self, request: HttpRequest) -> bool:
        return False