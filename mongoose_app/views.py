from django.shortcuts import render

def index(request):
    return render(request, "index.html")

# GET endpoints
@require_GET()
def get_card(request):
    return render(request, "index.html")

@require_GET()
def get_products(request):
    return render(request, "index.html")

# POST endpoints
@require_POST()
def create_transaction(request):
    return render(request, "index.html")

@require_POST()
def register_card(request):
    return render(request, "index.html")
