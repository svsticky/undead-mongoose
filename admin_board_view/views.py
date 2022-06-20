from django.shortcuts import render
from .models import *

def index(request):
    return render(request, "home.html")

def products(request):
    products = Product.objects.all()
    return render(request, "products.html", { "products": products })
