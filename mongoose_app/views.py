from django.shortcuts import render
from django.views.decorators.http import require_http_methods

def index(request):
    return render(request, "index.html")

# GET endpoints
@require_http_methods(["GET"])
def get_card(request):
    return render(request, "index.html")

@require_http_methods(["GET"])
def get_products(request):
    return render(request, "index.html")

# POST endpoints
@require_http_methods(["POST"])
def create_transaction(request):
    return render(request, "index.html")

@require_http_methods(["POST"])
def register_card(request):
    return render(request, "index.html")
