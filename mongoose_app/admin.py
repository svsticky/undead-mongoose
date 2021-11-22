from typing import Optional
from django.contrib import admin
from django.http.request import HttpRequest
from .models import Product, Category, SaleTransaction, TopUpTransaction, User, Card

# Register your models here.

admin.site.site_header = "Undead Mongoose Admin Platform"
admin.site.site_title = "Undead Mongoose Admin"
admin.site.index_title = "Welcome to Undead Mongoose"


class TopUpTransactionsInline(admin.TabularInline):
    model = TopUpTransaction
    extra = 1
    readonly_fields = ['added']

class SaleTransactionsInline(admin.TabularInline):
    model = SaleTransaction

    def has_add_permission(self, request: HttpRequest, obj) -> bool:
        return False

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    fields = ('user_id', 'name', 'age', 'euro_balance')
    list_display = ('name', 'age', 'euro_balance')
    readonly_fields = ['euro_balance']
    exclude = ['balance']
    inlines = [TopUpTransactionsInline, SaleTransactionsInline]
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'euro', 'category', 'image_view')
    readonly_fields = ['image_view']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    fields = ['name', 'alcoholic']


@admin.register(SaleTransaction)
class SaleTransactionAdmin(admin.ModelAdmin):
    
    def has_add_permission(self, request: HttpRequest) -> bool:
        return False


@admin.register(TopUpTransaction)
class TopUpTransactionAdmin(admin.ModelAdmin):
    
    fields = ('user_id', 'transaction_id', 'transaction_sum')
    readonly_fields = ['date']

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):

    fields = ['card_id', 'active', 'user_id']