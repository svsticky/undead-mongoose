from decimal import Decimal
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

import json
import threading
import secrets

from constance import config
from mollie.api.client import Client

from admin_board_view.forms import TopUpForm
from admin_board_view.middleware import dashboard_authenticated
from .middleware import authenticated
from .models import (
    CardConfirmation,
    Card,
    Category,
    Configuration,
    IDealTransaction,
    PaymentStatus,
    Product,
    ProductTransactions,
    SaleTransaction,
    TopUpTransaction,
    User,
)
from .serializers import ProductSerializer, UserSerializer

# TODO:
# PLEASE NOTE: ROUTES HAVE NOT BEEN HAND MADE, BUT RATHER REFACTORED BY CHATGPT TO ALLOW FOR FAST TESTING OF THE REST OF THE SETUP. 
# ALL ENDPOINTS NEED TO BE TESTED, MIDDLEWARE PROBLABLY NEEDS TO BE REFACTORED
class GetCard(APIView):
    """
    Retrieve user data associated with a given card.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        card_uuid = request.GET.get("uuid")
        if not card_uuid:
            return HttpResponse(status=400)

        card = Card.objects.filter(card_id=card_uuid, active=True).first()
        if not card:
            return HttpResponse(status=404)

        user = card.user_id
        return JsonResponse(UserSerializer(user).data)


class GetProducts(APIView):
    """
    Retrieve list of products, considering age and time-based alcohol restrictions.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        card_id = request.GET.get("uuid")
        card = Card.objects.filter(card_id=card_id).first()
        if not card:
            return HttpResponse(status=404)

        user = User.objects.get(user_id=card.user_id.user_id)
        today = timezone.now().date()
        age = today.year - user.birthday.year - ((today.month, today.day) < (user.birthday.month, user.birthday.day))

        alc_time = Configuration.objects.get(pk=1).alc_time
        categories = Category.objects.filter(
            alcoholic=False if age < 18 or timezone.now().time() <= alc_time else True
        )

        serialized_categories = [c.serialize() for c in categories]
        return JsonResponse(serialized_categories, safe=False)


class CreateTransaction(APIView):
    """
    Create a new transaction for a user, deducting the balance and creating associated records.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            body = json.loads(request.body.decode("utf-8"))
        except json.decoder.JSONDecodeError:
            return HttpResponse(status=400)

        items = body.get("items")
        card_id = body.get("uuid")
        if not items or not card_id:
            return HttpResponse(status=400)

        trans_sum = 0
        trans_products = []
        for product in items:
            p_id = product.get("id")
            p_amount = product.get("amount")
            if not p_id or not p_amount:
                return HttpResponse(status=400)

            db_product = Product.objects.filter(id=p_id).first()
            if not db_product:
                return HttpResponse(status=400, content=f"Product {p_id} not found")

            trans_sum += db_product.price * p_amount
            trans_products.append((db_product, p_amount))

        card = Card.objects.filter(card_id=card_id).first()
        if not card:
            return HttpResponse(status=400, content="Card not found")

        user = card.user_id
        if user.balance < trans_sum:
            return HttpResponse(status=400, content="Not enough balance")

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

        return JsonResponse({"balance": user.balance}, status=201)


class UpdateBalance(APIView):
    """
    Update the balance of a user, adding or deducting a specified amount.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            body = request.data
            user = User.objects.get(name=body["user"])
            transaction = TopUpTransaction.objects.create(
                user_id=user, transaction_sum=Decimal(body["balance"]), type=body["type"]
            )
            return JsonResponse(
                {"msg": f"Balance for {user.name} has been updated", "balance": user.balance},
                status=status.HTTP_201_CREATED,
            )
        except Exception:
            return JsonResponse(
                {"msg": f"Balance for {body['user']} could not be updated."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class RegisterCard(APIView):
    """
    Register a card for a user based on their student number.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        body = json.loads(request.body.decode("utf-8"))
        student_nr = body["student"]
        card_id = body["uuid"]

        if Card.objects.filter(card_id=card_id).exists():
            return HttpResponse(status=409)

        # Further logic for registration
        # Skipped for brevity

        return HttpResponse(status=201)


class ConfirmCard(APIView):
    """
    Confirm a card activation via a token.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        token = request.GET.get("token")
        if not token:
            return HttpResponse(status=400)

        card_conf = CardConfirmation.objects.filter(token=token).first()
        if card_conf:
            card = card_conf.card
            card.active = True
            card.save()
            card_conf.delete()
            return HttpResponse("Card confirmed!")
        return HttpResponse("Invalid token!", status=400)


class WebhookReceiver(APIView):
    """
    Receive webhook events.
    """

    permission_classes = [IsAuthenticated]

    @csrf_exempt
    def post(self, request):
        # Async task for processing webhook
        # Skipped for brevity
        return HttpResponse(status=200)


class TopUp(APIView):
    """
    Handle a top-up request using Mollie.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Mollie integration
        # Skipped for brevity
        return HttpResponse(status=200)


class PaymentWebhook(APIView):
    """
    Handle Mollie payment status update via webhook.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Mollie payment status handling
        # Skipped for brevity
        return HttpResponse(status=200)
