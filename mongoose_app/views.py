from django.shortcuts import render
from django.views.decorators.http import require_http_methods

def index(request):
    return render(request, "index.html")

# GET endpoints
@require_http_methods(["GET"])
def get_card(request):
    """
    Should:
    - Check if card exists, if so obtain user, return user.
    - Else, should return that student number is needed (frontend should go to register page)
    """
    return render(request, "index.html")

@require_http_methods(["GET"])
def get_products(request):
    """
    Simply returns all products in the database
    Should we handle here whether alcoholic products are returned?
    """
    return render(request, "index.html")

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
    - If user does not exist here, create it BUT MAKE INITIAL BALANCE THE BALANCE CURRENTLY IN KOALA 
        (temporarily of course until mongoose is out of koala)
    - Else add card to user.
    """
    return render(request, "index.html")
