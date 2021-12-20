import json
from django.http.response import Http404, HttpResponse
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from django.conf import settings
from .middleware import authenticated
from .models import Category, Card, Product, ProductTransactions, SaleTransaction, User
from datetime import datetime, date
from django.views.decorators.csrf import csrf_exempt
import requests
import threading
from constance import config
import sentry_sdk

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


@authenticated
@require_http_methods(["GET"])
def get_products(request):
    """
    Simply returns all products in the database
    Should we handle here whether alcoholic products are returned?
    """
    # Obtain user from card info
    card_id = request.GET.get('uuid')
    card = Card.objects.filter(card_id=card_id).first()
    user = User.objects.filter(user_id=card.user_id.user_id).first()
    # Calc age of user based on birthday
    today = date.today()
    age = today.year - user.birthday.year - ((today.month, today.day) < (user.birthday.month, user.birthday.day))

    now = datetime.now()
    if now.hour > config.BEER_HOUR and age > 17:
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
            product_vat=product.vat.percentage,
            amount=amount)

    return JsonResponse(
        {
            'balance': user.balance
        },
        status=201, safe=False)

@csrf_exempt
@authenticated
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
    # Obtain student number and card uuid from sloth
    body = json.loads(request.body.decode('utf-8'))
    student_nr = body['student']
    card_id = body['uuid']
    print(body)

    # Check if card is already present in the database
    # Cards are FULLY UNIQUE OVER ALL MEMBERS
    card = Card.objects.filter(card_id=card_id).first()
    
    if not card == None:
        return HttpResponse(status=409)

    # Obtain user information from Koala (or any other central member base)
    koala_response = requests.get(
        settings.USER_URL + '/api/internal/member_by_studentid',
        params={
            'student_number' : student_nr
        },
        headers={
            'Authorization' : settings.USER_TOKEN
        }
    )
    # If user is not found in database, we cannot create user here.
    if koala_response.status_code == 204:
        return HttpResponse(status=404) # Sloth expects a 404.

    # Get user info.
    koala_response = koala_response.json()
    user_id = koala_response['id']
    # Check if user exists.
    user = User.objects.filter(user_id=user_id).first()
    # If so, add the card to the already existing user.
    if not user == None:
        card = Card.objects.create(
            card_id=card_id,
            active=True,
            user_id=user
        )
    # Else, we first create the user based on the info from koala.
    else:
        first_name = koala_response['first_name']
        infix = koala_response['infix']
        last_name = koala_response['last_name']
        born = datetime.strptime(koala_response['birth_date'], '%Y-%m-%d')
        
        user = User.objects.create(
            user_id=user_id, 
            name=f'{first_name} {infix} {last_name}',
            birthday=born
        )
        card = Card.objects.create(
            card_id=card_id,
            active=True,
            user_id=user
        )
    # If that all succeeds, we return CREATED.
    return HttpResponse(status=201)

@csrf_exempt
@require_http_methods(["POST"])
def on_webhook(request):
    thr = threading.Thread(target=async_on_webhook, args=[request])
    thr.start()
    return HttpResponse(status=200)
    

def async_on_webhook(request):
    print("JOERT")
    koala_sent = json.loads(request.body.decode('utf-8'))

    if koala_sent['type'] == 'member':
        user_id = koala_sent['id']
        print(user_id)
        user = User.objects.filter(user_id=user_id).first()
        print(user.user_id)
        if not user == None:
            koala_response = requests.get(
                settings.USER_URL + '/api/internal/member_by_id',
                params={
                    'id' : user.user_id
                },
                headers= {
                    'Authorization' : settings.USER_TOKEN
                }
            )
            # TODO: What if this happens?
            if koala_response.status_code == 204:
                user.delete()
            print(koala_response.ok)
            if koala_response.ok:
                print(koala_response)
                koala_response = koala_response.json()
                first_name = koala_response['first_name']
                infix = koala_response['infix']
                last_name = koala_response['last_name']
                user.name = f'{first_name} {infix} {last_name}'
                user.birthday = datetime.strptime(koala_response['birth_date'], '%Y-%m-%d')
                user.save()

    # obtain id from webhook
    # check on type
    # get user linked to id
    # get information from koala through request
    # update user with that information
    return HttpResponse(status=200)
