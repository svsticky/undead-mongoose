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

    now = timezone.localtime(timezone.now())
    if now.time() > alc_time and age > 17:
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
    body = json.loads(request.body.decode("utf-8"))
    student_nr = body["student"]
    card_id = body["uuid"]

    # Check if card is already present in the database
    # Cards are FULLY UNIQUE OVER ALL MEMBERS
    card = Card.objects.filter(card_id=card_id).first()

    if not card == None:
        return HttpResponse(status=409)

    # Obtain user information from Koala (or any other central member base)
    koala_response = requests.get(
        settings.USER_URL + "/api/internal/member_by_studentid",
        params={"student_number": student_nr},
        headers={"Authorization": settings.USER_TOKEN},
    )
    # If user is not found in database, we cannot create user here.
    if koala_response.status_code == 204:
        return HttpResponse(status=404)  # Sloth expects a 404.

    # Get user info.
    koala_response = koala_response.json()
    user_id = koala_response["id"]
    # Check if user exists.
    user = User.objects.filter(user_id=user_id).first()
    # If so, add the card to the already existing user.
    if not user == None:
        card = Card.objects.create(card_id=card_id, active=False, user_id=user)
        send_confirmation(koala_response["email"], card)
    # Else, we first create the user based on the info from koala.
    else:
        first_name = koala_response["first_name"]
        infix = None
        if "infix" in koala_response:
            infix = koala_response["infix"]
        last_name = koala_response["last_name"]
        born = datetime.strptime(koala_response["birth_date"], "%Y-%m-%d")

        user = User.objects.create(
            user_id=user_id,
            name=f"{first_name} {infix} {last_name}"
            if infix
            else f"{first_name} {last_name}",
            birthday=born,
            email=koala_response["email"],
        )
        card = Card.objects.create(card_id=card_id, active=False, user_id=user)
        send_confirmation(koala_response["email"], card)
    # If that all succeeds, we return CREATED.
    return HttpResponse(status=201)


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
        user = User.objects.get(email=request.user)
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
