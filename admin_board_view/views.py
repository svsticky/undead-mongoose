from django.http.response import JsonResponse
from django.shortcuts import render
from .models import *


def index(request):
    return render(request, "home.html")


def products(request):
    if request.POST:
        product = ProductForm(request.POST, request.FILES)
        if product.is_valid():
            product.category = Category.objects.get(name=product.cleaned_data["category"])
            product.save()

    products = Product.objects.all()
    categories = Category.objects.all()
    return render(request, "products.html", { "products": products, "categories": categories, "image_upload": ProductForm })


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
