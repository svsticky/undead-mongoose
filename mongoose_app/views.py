from django.http.response import Http404, HttpResponse
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .middleware import authenticated
from .models import Category, Card
from datetime import datetime

def index(request):
    return render(request, "index.html")

# GET endpoints
@authenticated
@require_http_methods(["GET"])
def get_card(request):
    """
    Should:
    - Check if card exists, if so obtain user, return user.
    - Else, should return that student number is needed (frontend should go to register page)
    """
    if 'uuid' in request.GET:
        card_uuid = request.GET.get('uuid')
        card = Card.objects.filter(card_id=card_uuid).first()
        if card == None:
            return Http404
        user = card.user_id
        return JsonResponse(user.serialize(), safe=False)
    return HttpResponse(status=400)

#Probably needs a change due to what sloth expects atm.
@authenticated
@require_http_methods(["GET"])
def get_products(request):
    """
    Simply returns all products in the database
    Should we handle here whether alcoholic products are returned?
    """
    now = datetime.now()
    if now.hour >= 16:
        categories = Category.objects.all()
    else:
        categories = Category.objects.filter(alcoholic=False)
        
    
    serialized_categories = [c.serialize() for c in categories]
    return JsonResponse(serialized_categories, safe=False)

# POST endpoints
@require_http_methods(["POST"])
def create_transaction(request):
    """
    Called when user finishes transaction.
    Should:
    - Deduct amount from balance
    - Create a Transaction object.
    Would the current model setup not create a problem when a product is deleted?
    """
    return render(request, "index.html")

@require_http_methods(["POST"])
def register_card(request):
    """
    Reached when student number is entered for a certain card.
    Both should be provided in request.
    Then:
    - Ask koala for user info
    - If user does not exist here, create it
    - Else add card to user.
    """
    return render(request, "index.html")
