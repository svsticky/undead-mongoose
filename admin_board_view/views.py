from django.http.response import JsonResponse
from django.shortcuts import render, HttpResponseRedirect
from .models import *
import json


def index(request):
    product_amount = Product.objects.count()
    total_balance = sum(user.balance for user in User.objects.all())

    return render(request, "home.html", {"users": User.objects.all(), "product_amount": product_amount, "total_balance": total_balance })


def products(request):
    if request.POST:
        product = ProductForm(request.POST, request.FILES)

        if request.GET["id"] and request.GET["id"] != "0":
            instance = Product.objects.get(id=request.GET["id"])
            product = ProductForm(request.POST, request.FILES, instance=instance)

        if product.is_valid():
            product.category = Category.objects.get(name=product.cleaned_data["category"])
            p = product.save()
            return HttpResponseRedirect("/products?id="+str(p.id))

    product = None
    pf = ProductForm
    if request.GET and request.GET["id"] and request.GET["id"] != "0":
        product = Product.objects.get(id=request.GET["id"])
        pf = ProductForm(initial={"image": "Test"}, instance=product)

    products = Product.objects.all()
    categories = Category.objects.all()
    return render(request, "products.html", { "products": products, "categories": categories, "product_form": pf, "current_product": product })


def edit(request):
    id = request.POST.dict()['id']
    product = Product.objects.get(id=id)

    # Do some product editing stuff
    
    return JsonResponse({ "msg": f"Edited the product with id {product.id}" })


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
        sales= SaleTransaction.objects.all().filter(user_id=user)

        cards = []
        for i, card in enumerate(Card.objects.all().filter(user_id=user.id)):
            cards.append({"info": card})
            if card.active == False:
                cards[i]["token"] = CardConfirmation.objects.get(card=card).token

        return render(request, "user.html", { "user_info": user, "cards": cards, "top_ups": top_ups, "sales": sales })
    else:
        users = User.objects.all()
        return render(request, "user.html", { "users": users })


def settings(request):
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
            elif "delete" in category and category["delete"] == True:
                cat = Category.objects.get(id=category["id"])
                cat.delete()
            else:
                cat = Category.objects.get(id=category["id"])
                cat.name = category["name"]
                cat.alcoholic = category["checked"]
                cat.save()

        return JsonResponse({ "msg": f"Updated the mongoose categories" })
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
            elif "delete" in vat and vat["delete"] == True:
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
    sales = list(SaleTransaction.objects.all())
    topups = list(TopUpTransaction.objects.all())
    transactions = sales + topups
    return render(request, "transactions.html", { "transactions": transactions })
