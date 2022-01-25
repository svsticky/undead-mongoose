from datetime import datetime
import json
from django.http import JsonResponse
from django.http.response import HttpResponseRedirect
from django.urls import path
from django.utils.safestring import mark_safe
from django.contrib import admin
from django.http.request import HttpRequest
from django.contrib import messages
from .models import VAT, Product, Category, ProductTransactions, SaleTransaction, TopUpTransaction, User, Card

# Register your models here.

admin.site.site_header = "Undead Mongoose Admin Platform"
admin.site.site_title = "Undead Mongoose Admin"
admin.site.index_title = "Welcome to Undead Mongoose"


class ProductTransactionsInline(admin.TabularInline):
    model = ProductTransactions
    extra = 0
    fields = ['product_id', 'transaction_id', 'show_price', 'show_vat', 'amount']
    readonly_fields = ['product_id', 'transaction_id', 'show_price', 'show_vat', 'amount']

    def has_delete_permission(self, request: HttpRequest, obj = None) -> bool:
        return False

    def has_add_permission(self, request: HttpRequest, obj) -> bool:
        return False

class ProductInline(admin.TabularInline):
    model = Product
    extra = 1
    fields = ['name', 'price', 'image', 'image_view']
    readonly_fields = ['image_view']

class CardInline(admin.TabularInline):
    model = Card
    extra = 0
    fields = ['card_id', 'active']
    readonly_fields = ['card_id']

class TopUpTransactionsInline(admin.TabularInline):
    model = TopUpTransaction
    extra = 1
    fields = ['id', 'transaction_sum', 'added']
    readonly_fields = ['id', 'added']

class SaleTransactionsInline(admin.TabularInline):
    model = SaleTransaction
    fields = ['id', 'transaction_sum', 'added']
    readonly_fields = ['id', 'transaction_sum', 'added']
    show_change_link = True

    def has_add_permission(self, request: HttpRequest, obj) -> bool:
        return False

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    fields = ('user_id', 'name', 'birthday', 'euro_balance')
    list_display = ('name', 'birthday', 'euro_balance')
    readonly_fields = ['euro_balance', 'birthday', 'user_id', 'name']
    exclude = ['balance']
    inlines = [TopUpTransactionsInline, SaleTransactionsInline, CardInline]
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'euro', 'vat', 'category', 'image_view')
    readonly_fields = ['image_view']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    fields = ['name', 'alcoholic']
    inlines = [ProductInline]


@admin.register(SaleTransaction)
class SaleTransactionAdmin(admin.ModelAdmin):

    change_list_template = "admin/saletransactions/st_changelist.html"
    fields = ['id', 'user_id', 'transaction_sum', 'date']
    readonly_fields = ['date', 'id']
    inlines = [ProductTransactionsInline]
    
    def has_add_permission(self, request: HttpRequest) -> bool:
        return False
    
    def get_urls(self):
        urls = super().get_urls()
        export_url = [
            path('export/', self.export)
        ]
        return export_url + urls
    
    def export(self, request):           
        date_string = request.body.decode('utf-8').split('&')[1].split('=')[1]
        if len(date_string) == 0:
            messages.error(request, "You need to supply an export date!")
            return HttpResponseRedirect("../")
        date = datetime.strptime(date_string, '%Y-%m-%d').date()
        transactions = SaleTransaction.objects.filter(date=date).all()
        serialized_trans = [t.serialize() for t in transactions]
        # mark_safe(f"""
        #     <input text="text" id="submit" value="{json_trans}" style="position: absolute; top: -10000px">
        #     <a href="#" onclick="document.querySelector(\'#{btn_id}\').select(); document.execCommand(\'copy\');" class="addlink">Copy media url to clipboard</a>
        #     """
        # )
        return JsonResponse(serialized_trans, safe=False)



@admin.register(TopUpTransaction)
class TopUpTransactionAdmin(admin.ModelAdmin):
    
    fields = ('id', 'user_id', 'transaction_sum')
    readonly_fields = ['date', 'id']

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):

    fields = ['card_id', 'active', 'user_id']

@admin.register(VAT)
class VATAdmin(admin.ModelAdmin):
    list_display = ['id', 'percentage_view']
    readonly_fields = ['id']
