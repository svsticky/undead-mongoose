from django.http.response import JsonResponse
from django.shortcuts import render
from .models import *

def index(request):
    return render(request, "home.html")

def products(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    return render(request, "products.html", { "products": products, "categories": categories })

# Endpoints for altering models
def create(request):
    body = request.POST.dict()

    product = Product(
        name=body["name"],
        price=body["price"],
        category=body["category"],
        vat=body["vat"],
        enabled=body["enabled"],
        image=body["image"]
    )

    product.save()

    return JsonResponse({ "msg": f"Added new product with id {product.id}" })

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
