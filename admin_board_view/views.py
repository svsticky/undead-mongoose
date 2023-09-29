from django.db.models import Sum
from django.core.paginator import Paginator
from django.http.response import JsonResponse
from django.shortcuts import render, HttpResponseRedirect
from itertools import groupby
from .models import *
import json


def index(request):
    product_amount = Product.objects.count()
    total_balance = sum(user.balance for user in User.objects.all())
    return render(request, "home.html", {"users": User.objects.all(), "product_amount": product_amount, "total_balance": total_balance, "top_types": top_up_types })


def products(request):
    if request.POST:
        product = ProductForm(request.POST, request.FILES)

        if "edit" in request.GET and request.GET["edit"] != "0":
            instance = Product.objects.get(id=request.GET["edit"])
            product = ProductForm(request.POST, request.FILES, instance=instance)

        if product.is_valid():
            product.category = Category.objects.get(name=product.cleaned_data["category"])
            product.save()
            return HttpResponseRedirect("/products")

    product, product_sales = None, None
    pf = ProductForm
    if request.GET:
        if "edit" in request.GET and request.GET["edit"] != "0":
            product = Product.objects.get(id=request.GET["edit"])
            pf = ProductForm(instance=product)
        if "sales" in request.GET and request.GET["sales"] != "0":
            product = Product.objects.get(id=request.GET["sales"])
            transactions = ProductTransactions.objects.filter(product_id=product)
            product_sales = {
                "all": transactions,
                "sum": transactions.values('product_price').annotate(sum=Sum('amount'))
            }

    products = Product.objects.all()
    categories = Category.objects.all()
    return render(request, "products.html", { "products": products, "categories": categories, "product_form": pf, "current_product": product, "product_sales": product_sales })


def delete(request):
    id = request.POST.dict()['id']
    Product.objects.get(id=id).delete()
    return JsonResponse({ "msg": f"Deleted product with {id}" })


def toggle(request):
    id = request.POST.dict()['id']
    product = Product.objects.get(id=id)
    product.enabled = not product.enabled
    product.save()
    return JsonResponse({ "msg": f"Set the state of product {id} to enabled={product.enabled}" })


def users(request, user_id=None):
    user, cards = None, None
    if user_id:
        user = User.objects.get(id=user_id)
        top_ups = TopUpTransaction.objects.all().filter(user_id=user)
        product_sales = list(ProductTransactions.objects.all().filter(transaction_id__user_id=user))
        product_sale_groups = []
        for designation, member_group in groupby(product_sales, lambda sale: sale.transaction_id):
            product_sale_groups.append({ "key": designation, "values": list(member_group) })

        cards = []
        for i, card in enumerate(Card.objects.all().filter(user_id=user.id)):
            cards.append({"info": card})
            if card.active is False:
                cards[i]["token"] = CardConfirmation.objects.get(card=card).token

            top_ups_paginator = Paginator(top_ups, 5)
            try:
                top_up_page = top_ups_paginator.get_page(request.GET.get('top_ups'))
            except Exception:
                top_up_page = top_ups_paginator.page(1)

            sales_paginator = Paginator(product_sale_groups, 5)
            try:
                sales_page = sales_paginator.get_page(request.GET.get('sales'))
            except Exception:
                sales_page = sales_paginator.page(1)

        return render(request, "user.html", { "user_info": user, "cards": cards, "top_ups": top_up_page, "sales": sales_page, "top_types": top_up_types })
    else:
        users = User.objects.all()
        return render(request, "user.html", { "users": users })


def settings_page(request):
    vat = VAT.objects.all()
    categories = Category.objects.all()
    return render(request, "settings.html", { "vat": vat, "categories": categories })


def category(request):
    try:
        categories = json.loads(request.POST.dict()['categories'])
        for category in categories:
            if category["id"] == '0':
                cat = Category.objects.create(name=category["name"], alcoholic=category["checked"])
                cat.save()
            elif "delete" in category and category["delete"] is True:
                cat = Category.objects.get(id=category["id"])
                cat.delete()
            else:
                cat = Category.objects.get(id=category["id"])
                cat.name = category["name"]
                cat.alcoholic = category["checked"]
                cat.save()

        return JsonResponse({ "msg": "Updated the mongoose categories" })
    except Exception as e:
        print(e)
        return JsonResponse({ "msg": "Something went wrong whilst trying to save the categories" }, status=400)


def vat(request):
    try:
        vatBody = json.loads(request.POST.dict()['vat'])
        for vat in vatBody:
            if vat["id"] == '0':
                newVAT = VAT.objects.create(percentage=vat["percentage"])
                newVAT.save()
            elif "delete" in vat and vat["delete"] is True:
                delVAT = VAT.objects.get(id=vat["id"])
                delVAT.delete()
            else:
                newVAT = VAT.objects.get(id=vat["id"])
                newVAT.percentage = vat["percentage"]
                newVAT.save()

        return JsonResponse({ "msg": f"Updated the mongoose VAT percentages" })
    except Exception as e:
        print(e)
        return JsonResponse({ "msg": "Something went wrong whilst trying to save the VAT percentages" }, status=400)


def transactions(request):
    # Top up paginator
    top_ups = list(TopUpTransaction.objects.all())
    top_ups_paginator = Paginator(top_ups, 5)
    try:
        top_up_page = top_ups_paginator.get_page(request.GET.get('top_ups'))
    except Exception:
        top_up_page = top_ups_paginator.page(1)

    # Product sale paginator
    product_sales = list(ProductTransactions.objects.all())
    product_sale_groups = []
    for designation, member_group in groupby(product_sales, lambda sale: sale.transaction_id):
        product_sale_groups.append({ "key": designation, "values": list(member_group) })

    sales_paginator = Paginator(product_sale_groups, 10)
    try:
        sales_page = sales_paginator.get_page(request.GET.get('sales'))
    except Exception:
        sales_page = sales_paginator.page(1)

    return render(request, "transactions.html", { "top_ups": top_up_page, "sales": sales_page })
