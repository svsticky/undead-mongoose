import json
from django.http.response import HttpResponse
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from django.conf import settings
from .middleware import authenticated
from .models import CardConfirmation, Category, Card, Product, ProductTransactions, SaleTransaction, User, NamedTransactionProductTotal
from datetime import datetime, date
from django.views.decorators.csrf import csrf_exempt
import requests
import threading
from constance import config
import secrets

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
        card = Card.objects.filter(card_id=card_uuid, active=True).first()
        if card == None:
            return HttpResponse(status=404)
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
    if now.time() > config.BEER_HOUR and age > 17:
        categories = Category.objects.all()
    else:
        categories = Category.objects.filter(alcoholic=False)
        
    
    serialized_categories = [c.serialize() for c in categories]
    return JsonResponse(serialized_categories, safe=False)

@authenticated
@require_http_methods(['GET'])
def get_product_transactions(request):
    """
    Retrieve all historical sale transactions
    """
    query_for_date_str = request.GET.get('date')
    if query_for_date_str:
        query_for_dt = datetime.fromtimestamp(int(query_for_date_str))
    else:
        query_for_dt = datetime.now()
    query_for_date = datetime(query_for_dt.year, query_for_dt.month, query_for_dt.day)

    transactions = ProductTransactions.objects.all()

    product_counts = {}
    product_names = {}

    for transaction_product in transactions:
        transaction = transaction_product.transaction_id

        transaction_dt = datetime(transaction.date.year, transaction.date.month, transaction.date.day)

        if transaction_dt != query_for_date:
            continue

        product = transaction_product.product_id

        if product.id in product_counts:
            product_counts[product.id] = product_counts[product.id] + 1
        else:
            product_counts[product.id] = 1

        if product.id not in product_names:
            product_names[product.id] = product.name

    result = []

    for product_id in product_counts:
        result.append(NamedTransactionProductTotal(
            product_id=product_id,
            amount=product_counts[product_id],
            name=product_names[product_id]
        ))

    serialized_result = [c.serialize() for c in result]
    return JsonResponse(serialized_result, safe=False)


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

    if not items:
        return HttpResponse(status=400)

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
            active=False,
            user_id=user
        )
        send_confirmation(koala_response['email'], card)
    # Else, we first create the user based on the info from koala.
    else:
        first_name = koala_response['first_name']
        infix = None
        if 'infix' in koala_response:
            infix = koala_response['infix']
        last_name = koala_response['last_name']
        born = datetime.strptime(koala_response['birth_date'], '%Y-%m-%d')
        
        user = User.objects.create(
            user_id=user_id, 
            name=f'{first_name} {infix} {last_name}' if infix else f'{first_name} {last_name}',
            birthday=born
        )
        card = Card.objects.create(
            card_id=card_id,
            active=False,
            user_id=user
        )
        send_confirmation(koala_response['email'], card)
    # If that all succeeds, we return CREATED.
    return HttpResponse(status=201)


@require_http_methods(["GET"])
def confirm_card(request):
    if 'token' in request.GET:
        token = request.GET.get('token')
        card_conf = CardConfirmation.objects.filter(token=token).first()
        if card_conf:
            card = card_conf.card
            card.active = True
            card.save()
            card_conf.delete()
            return HttpResponse('Card confirmed!')
        else:
            return HttpResponse('Something went horribly wrong!')
    else:
        return HttpResponse('You should not have requested this url')


@csrf_exempt
@require_http_methods(["POST"])
def on_webhook(request):
    thr = threading.Thread(target=async_on_webhook, args=[request])
    thr.start()
    return HttpResponse(status=200)
    


def async_on_webhook(request):
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
                infix = koala_response['infix'] if 'infix' in koala_response else ""
                last_name = koala_response['last_name']
                user.name = f'{first_name} {infix} {last_name}'
                user.birthday = datetime.strptime(koala_response['birth_date'], '%Y-%m-%d')
                user.save()

    return HttpResponse(status=200)


# Mailgun send function.
def send_confirmation(email, card):
    # build token
    token = secrets.token_hex(16)
    CardConfirmation.objects.create(card=card, token=token)

    requests.post(
        f'https://api.mailgun.net/v3/{settings.MAILGUN_ENV}/messages',
        auth=('api', settings.MAILGUN_TOKEN),
        data={
            'from': f'Undead Mongoose <noreply@{settings.MAILGUN_ENV}>',
            'to': email,
            'subject': 'Mongoose Card Confirmation',
            'text':
                f"""
                Beste sticky lid,

                Je hebt zojuist een nieuwe kaart gekoppeld aan het mongoose vreet/zuipsysteem.
                Om je kaart te koppelen, volg de volgende link:
                {settings.BASE_URL}/confirm?token={token}

                Met vriendelijke groetjes,
                BESTUUUUUUUUUUR
                """
        }
    )
