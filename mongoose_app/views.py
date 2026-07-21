import json
from django.http.response import HttpResponse
from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from decimal import Decimal
from django.conf import settings

from admin_board_view.forms import TopUpForm
from admin_board_view.middleware import dashboard_authenticated
from .middleware import authenticated
from .models import (
    CardConfirmation,
    Category,
    Card,
    IDealTransaction,
    PaymentStatus,
    Product,
    ProductTransactions,
    SaleTransaction,
    TopUpTransaction,
    User,
    Configuration,
)
from datetime import datetime, date
from django.views.decorators.csrf import csrf_exempt
import requests
import threading
from constance import config
from django.utils import timezone
from mollie.api.client import Client

import secrets


# GET endpoints
@require_http_methods(["GET", "DELETE"])
def card(request):
    return get_card(request) if request.method == "GET" else delete_card(request)

@authenticated
def get_card(request):
    """
    Should:
    - Check if card exists, if so obtain user, return user.
    - Else, should return that student number is needed (frontend should go to register page)
    """
    if "uuid" in request.GET:
        card_uuid = request.GET.get("uuid")
        card = Card.objects.filter(card_id=card_uuid, active=True).first()
        if card is None:
            return HttpResponse(status=404)

        card.last_used = timezone.now()
        card.save()

        user = card.user_id
        return JsonResponse(user.serialize(), safe=False)
    return HttpResponse(status=400)

@dashboard_authenticated
def delete_card(request):
    """
    Expects:
    - a session
    - card uuid in GET params
    Should:
    - Check if the card belongs to the user or the user is an admin
    - Delete the card from the database
    """
    card_uuid = request.GET.get("uuid")
    card = Card.objects.filter(card_id = card_uuid, active=True).first()
    if card is None:
        return HttpResponse("Unknown card uuid", status=404)

    card_user: User = card.user_id
    if request.user.is_superuser or card_user.email == request.user.email:
        card.delete()
        return HttpResponse(status=200)

    return HttpResponse("Card owner and session user do not match", status=403)

@dashboard_authenticated
def change_card_name(request):
    """
    - Check if card exists and belongs to the user (or user is an admin)
    - Update card name to new card name
    """
    if "card_uuid" in request.GET:
        # Get card info, check if card exists
        card_uuid = request.GET.get("card_uuid")
        card = Card.objects.filter(card_id=card_uuid, active=True).first()
        if card is None:
            return HttpResponse(status=404)

        # Check if card belongs to user or user is admin
        card_user: User = card.user_id
        if "name" in request.GET and (request.user.is_superuser or card_user.email == request.user.email):
            # Update card name
            card.card_name = request.GET.get("name")
            card.save()

        return HttpResponse(status=200)
    return HttpResponse(status=400)

@authenticated
@require_http_methods(["GET"])
def get_products(request):
    """
    Simply returns all products in the database
    Should we handle here whether alcoholic products are returned?
    """
    # Obtain user from card info
    card_id = request.GET.get("uuid")
    card = Card.objects.filter(card_id=card_id).first()
    user = User.objects.filter(user_id=card.user_id.user_id).first()
    # Calc age of user based on birthday
    today = date.today()
    age = (
        today.year
        - user.birthday.year
        - ((today.month, today.day) < (user.birthday.month, user.birthday.day))
    )
    alc_time = Configuration.objects.get(pk=1).alc_time

    user_favorites = user.favorites.filter(enabled=True)
    now = timezone.localtime(timezone.now())

    if now.time() > alc_time and age > 17:
        categories = Category.objects.all()
    else:
        categories = Category.objects.filter(alcoholic=False)
        user_favorites = user_favorites.filter(category__alcoholic=False)

    serialized_categories = [c.serialize() for c in categories]
    
    fav_category = {
        "name": "⭐",
        "products": [p.serialize() for p in user_favorites]
    }
    serialized_categories.insert(0, fav_category)

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

    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.decoder.JSONDecodeError:
        return HttpResponse(status=400)

    if "items" not in body or "uuid" not in body:
        return HttpResponse(status=400)

    items = body["items"]
    card_id = body["uuid"]

    trans_products = []
    trans_sum = 0
    for product in items:
        if "id" not in product or "amount" not in product:
            return HttpResponse(status=400)

        p_id = int(product["id"])
        p_amount = int(product["amount"])

        db_product = Product.objects.filter(id=p_id).first()
        if not db_product:
            return HttpResponse(status=400, content=f"Product {p_id} not found")

        trans_sum += db_product.price * p_amount
        trans_products.append((db_product, p_amount))

    card = Card.objects.filter(card_id=card_id).first()
    if not card:
        return HttpResponse(status=400, content="Card not found")

    user = card.user_id
    if user.balance - trans_sum < 0:
        return HttpResponse(
            status=400, content="Transaction failed, not enough balance"
        )

    transaction = SaleTransaction.objects.create(
        user_id=user, transaction_sum=trans_sum
    )

    for product, amount in trans_products:
        ProductTransactions.objects.create(
            product_id=product,
            transaction_id=transaction,
            product_price=product.price,
            product_vat=product.vat.percentage,
            amount=amount,
        )

    return JsonResponse({"balance": user.balance}, status=201, safe=False)


@require_http_methods(["POST"])
def update_balance(request):
    """
    Called when user finishes transaction.
    Should:
    - Add or deduct amount from balance
    - Create a Transaction object
    """
    try:
        body = request.POST.dict()
        user = User.objects.get(name=body["user"])

        transaction = TopUpTransaction.objects.create(
            user_id=user, transaction_sum=Decimal(body["balance"]), type=body["type"]
        )
        transaction.save()

        return JsonResponse(
            {
                "msg": f"Balance for {user.name} has been updated to {user.balance}",
                "balance": user.balance,
            },
            status=201,
            safe=False,
        )
    except Exception as e:
        return JsonResponse(
            {"msg": f"Balance for {body['user']} could not be updated."},
            status=400,
            safe=False,
        )


def get_keycloak_user_by_id(user_id):
    """
    Retrieves user information from Keycloak by Keycloak User ID (UUID) using Client Credentials.
    """
    keycloak_url = getattr(settings, "KEYCLOAK_URL", None)
    realm = getattr(settings, "KEYCLOAK_REALM", None)
    client_id = getattr(settings, "KEYCLOAK_CLIENT_ID", None)
    client_secret = getattr(settings, "KEYCLOAK_CLIENT_SECRET", None)

    if not all([keycloak_url, realm, client_id, client_secret]):
        return None

    try:
        token_url = f"{keycloak_url.rstrip('/')}/realms/{realm}/protocol/openid-connect/token"
        token_data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        access_token = token_response.json()["access_token"]

        user_url = f"{keycloak_url.rstrip('/')}/admin/realms/{realm}/users/{user_id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        user_response = requests.get(user_url, headers=headers)
        if user_response.status_code == 200:
            return user_response.json()
    except Exception as e:
        print(f"Keycloak query by id failed: {e}")

    return None


def get_keycloak_user_by_student_number(student_number):
    """
    Retrieves user information from Keycloak using Client Credentials.
    """
    keycloak_url = getattr(settings, "KEYCLOAK_URL", None)
    realm = getattr(settings, "KEYCLOAK_REALM", None)
    client_id = getattr(settings, "KEYCLOAK_CLIENT_ID", None)
    client_secret = getattr(settings, "KEYCLOAK_CLIENT_SECRET", None)

    if not all([keycloak_url, realm, client_id, client_secret]):
        raise ValueError("Keycloak configuration is incomplete in settings.")

    # 1. Obtain Access Token
    token_url = f"{keycloak_url.rstrip('/')}/realms/{realm}/protocol/openid-connect/token"
    token_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    token_response = requests.post(token_url, data=token_data)
    token_response.raise_for_status()
    access_token = token_response.json()["access_token"]

    # 2. Query Keycloak User
    users_url = f"{keycloak_url.rstrip('/')}/admin/realms/{realm}/users"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    params = {
        "q": f"student_number:{student_number}"
    }
    users_response = requests.get(users_url, headers=headers, params=params)
    users_response.raise_for_status()
    users_list = users_response.json()
    
    if not users_list:
        return None
        
    for u in users_list:
        attributes = u.get("attributes", {})
        std_num_list = attributes.get("student_number", [])
        if std_num_list and str(std_num_list[0]) == str(student_number):
            return u
            
    return users_list[0]


@csrf_exempt
@authenticated
@require_http_methods(["POST"])
def register_card(request):
    """
    Reached when student number is entered for a certain card.
    Both should be provided in request.
    Then:
    - Ask keycloak for user info
    - If user does not exist here, create it
    - Else add card to user.
    """
    # Obtain student number and card uuid from sloth
    body = json.loads(request.body.decode("utf-8"))
    student_nr = body["student"]
    card_id = body["uuid"]

    # Check if card is already present in the database
    # Cards are FULLY UNIQUE OVER ALL MEMBERS
    card = Card.objects.filter(card_id=card_id).first()

    if not card == None:
        return HttpResponse(status=409)

    try:
        keycloak_user = get_keycloak_user_by_student_number(student_nr)
    except Exception as e:
        print(f"Keycloak query failed: {e}")
        return HttpResponse("Internal server error during user lookup", status=500)

    if keycloak_user is None:
        return HttpResponse(status=404)  # Sloth expects a 404.

    email = keycloak_user.get("email")
    kc_id = keycloak_user.get("id") or str(student_nr)

    # Check if user exists by Keycloak ID
    user = User.objects.filter(user_id=kc_id).first()
    if user is None:
        user = User.objects.create(
            user_id=kc_id,
            balance=Decimal("0.00"),
        )

    card = Card.objects.create(card_id=card_id, active=False, user_id=user)
    if email:
        send_confirmation(email, card)

    return HttpResponse(status=200)


@require_http_methods(["GET"])
def confirm_card(request):
    if "token" in request.GET:
        token = request.GET.get("token")
        card_conf = CardConfirmation.objects.filter(token=token).first()
        if card_conf:
            card = card_conf.card
            card.active = True
            card.save()
            card_conf.delete()
            return HttpResponse("Card confirmed!")
        else:
            return HttpResponse("Something went horribly wrong!")
    else:
        return HttpResponse("You should not have requested this url")


@csrf_exempt
@require_http_methods(["POST"])
def on_webhook(request):
    thr = threading.Thread(target=async_on_webhook, args=[request])
    thr.start()
    return HttpResponse(status=200)


def async_on_webhook(request):
    koala_sent = json.loads(request.body.decode("utf-8"))

    if koala_sent["type"] == "member":
        user_id = koala_sent["id"]
        print(user_id)
        user = User.objects.filter(user_id=user_id).first()
        print(user.user_id)
        if not user is None:
            koala_response = requests.get(
                settings.USER_URL + "/api/internal/member_by_id",
                params={"id": user.user_id},
                headers={"Authorization": settings.USER_TOKEN},
            )
            # TODO: What if this happens?
            if koala_response.status_code == 204:
                user.delete()
            print(koala_response.ok)
            if koala_response.ok:
                print(koala_response)
                koala_response = koala_response.json()
                first_name = koala_response["first_name"]
                infix = koala_response["infix"] if "infix" in koala_response else ""
                last_name = koala_response["last_name"]
                user.name = f"{first_name} {infix} {last_name}"
                user.birthday = datetime.strptime(
                    koala_response["birth_date"], "%Y-%m-%d"
                )
                user.save()

    return HttpResponse(status=200)


# Mailgun send function.
def send_confirmation(email, card):
    # build token
    token = secrets.token_hex(16)
    CardConfirmation.objects.create(card=card, token=token)

    requests.post(
        f"https://api.mailgun.net/v3/{settings.MAILGUN_ENV}/messages",
        auth=("api", settings.MAILGUN_TOKEN),
        data={
            "from": f"Undead Mongoose <noreply@{settings.MAILGUN_ENV}>",
            "to": email,
            "subject": "Mongoose Card Confirmation",
            "text": f"""
                Beste sticky lid,

                Je hebt zojuist een nieuwe kaart gekoppeld aan Mongoose.
                Om je kaart te koppelen, volg de volgende link:
                {settings.BASE_URL}/api/confirm?token={token}

                Kusjes en knuffels,
                Sticky bestuur
                """,
        },
    )


@dashboard_authenticated
@require_http_methods(["POST"])
def topup(request):
    mollie_client = Client()
    mollie_client.set_api_key(settings.MOLLIE_API_KEY)
    bound_form = TopUpForm(request.POST)

    if bound_form.is_valid():
        user = User.objects.get(user_id=request.user.username)
        transaction_amount = bound_form.cleaned_data["amount"]
        transaction = IDealTransaction.objects.create(
            user_id=user, transaction_sum=transaction_amount
        )

        webhook_url = request.build_absolute_uri(
            f"/api/payment/webhook?transaction_id={transaction.transaction_id}"
        )
        redirect_url = request.build_absolute_uri(
            f"/?transaction_id={transaction.transaction_id}"
        )

        payment = mollie_client.payments.create(
            {
                "amount": {
                    "currency": "EUR",
                    "value": f"{(transaction_amount + settings.TRANSACTION_FEE):.2f}",
                },
                "description": "Top up mongoose balance",
                "redirectUrl": redirect_url,
                "webhookUrl": webhook_url,
                "method": "ideal",
            }
        )
        return redirect(payment.checkout_url)
    else:
        return redirect("/?error=1")


@csrf_exempt
@require_http_methods(["POST"])
def payment_webhook(request):
    mollie_client = Client()
    mollie_client.set_api_key(settings.MOLLIE_API_KEY)
    payment = mollie_client.payments.get(request.POST["id"])

    transaction_id = request.GET["transaction_id"]
    transaction = IDealTransaction.objects.get(transaction_id=transaction_id)

    if payment.is_paid():
        transaction.status = PaymentStatus.PAID
    elif payment.is_pending():
        transaction.status = PaymentStatus.PENDING
    elif payment.is_open():
        transaction.status = PaymentStatus.OPEN
    else:
        transaction.status = PaymentStatus.CANCELLED

    transaction.save()

    return HttpResponse(status=200)

@csrf_exempt
@authenticated
@require_http_methods(["POST"])
def toggle_favorite(request):
    """
    Toggles a product in the user's favorites list.
    Expects a JSON body with 'uuid' (card identifier) and 'product_id'.
    If the product is already a favorite, it is removed; otherwise, it is added.
    """
    try:
        body = json.loads(request.body.decode("utf-8"))
        product_id = body.get("product_id")
        card_id = body.get("uuid")
    except (json.decoder.JSONDecodeError, KeyError):
        return HttpResponse(status=400)

    card = Card.objects.filter(card_id=card_id).first()
    if not card:
        return HttpResponse("Card not found", status=404)
    
    user = card.user_id
    
    product = Product.objects.filter(id=product_id).first()
    if not product:
        return HttpResponse("Product not found", status=404)

    if product in user.favorites.all():
        user.favorites.remove(product)
        status = "removed"
    else:
        user.favorites.add(product)
        status = "added"

    return JsonResponse({"status": status, "product_id": product_id}, status=200)
