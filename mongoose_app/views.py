import json
from django.http.response import Http404, HttpResponse
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .middleware import authenticated
from .models import Category, Card, Product, ProductTransactions, SaleTransaction, User
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt

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
@csrf_exempt
@authenticated
@require_http_methods(["POST"])
def create_transaction(request):
    """
    Called when user finishes transaction.
    Should:
    - Deduct amount from balance
    - Create a Transaction object.
    Would the current model setup not create a problem when a product is deleted?
    """
    body = json.loads(request.body.decode('utf-8'))
    items = body['items']
    card_id = body['uuid']
    trans_products = []
    trans_sum = 0
    for product in items:
        p_id = int(product['id'])
        p_amount = int(product['amount'])
        db_product = Product.objects.filter(id=p_id).first()
        trans_sum += db_product.price * p_amount
        trans_products.append((db_product, p_amount))

    card = Card.objects.filter(card_id=card_id).first()
    user = card.user_id
    
    transaction = SaleTransaction.objects.create(
        user_id=user, 
        transaction_sum=trans_sum)

    for product, amount in trans_products:
        ProductTransactions.objects.create(
            product_id=product,
            transaction_id=transaction,
            product_price=product.price,
            amount=amount)

    return JsonResponse(
        {
            'balance': user.balance
        },
        status=201, safe=False)

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
    body = json.loads(request.body.decode('utf-8'))
    student_nr = body['student']
    card_id = body['uuid']

    # get student info based on student_nr in koala.
    # then, check if user already exists here,
    # If not, add, if so, update.
    return render(request, "index.html")
