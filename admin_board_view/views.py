import json

from django.db.models import Sum
from django.http.response import JsonResponse
from django.shortcuts import render, HttpResponseRedirect
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
from itertools import groupby

from admin_board_view.middleware import dashboard_authenticated, dashboard_admin
from admin_board_view.utils import create_paginator
from .models import *
from mollie.api.client import Client
from django.conf import settings
from .forms import TopUpForm


@dashboard_authenticated
def index(request):
    if request.user.is_superuser:
        product_amount = Product.objects.count()
        total_balance = sum(user.balance for user in User.objects.all())
        return render(
            request,
            "home.html",
            {
                "users": User.objects.all(),
                "product_amount": product_amount,
                "total_balance": total_balance,
                "top_types": top_up_types,
            },
        )
    else:
        user = User.objects.get(email=request.user.email)

        # Get product sales
        product_sales = list(
            ProductTransactions.objects.all().filter(transaction_id__user_id=user)
        )
        product_sale_groups = []
        for designation, member_group in groupby(
            product_sales, lambda sale: sale.transaction_id
        ):
            product_sale_groups.append(
                {"key": designation, "values": list(member_group)}
            )
        sales_page = create_paginator(product_sale_groups, request.GET.get("sales"))

        transaction_id = request.GET.dict().get("transaction_id")
        transaction = (
            IDealTransaction.objects.get(transaction_id=transaction_id)
            if transaction_id
            else None
        )

        # Get topup page
        top_ups = (
            TopUpTransaction.objects.all()
            .filter(user_id=user)
            .values_list("date", "transaction_sum")
        )
        ideal_transactions = (
            IDealTransaction.objects.all()
            .filter(user_id=user, status=PaymentStatus.PAID)
            .values_list("date", "transaction_sum")
        )
        all_top_ups = sorted(
            [(d, t, "Pin") for d, t in top_ups]
            + [(d, t, "iDeal") for d, t in ideal_transactions],
            key=lambda transaction: transaction[0],
        )
        top_up_page = create_paginator(all_top_ups, request.GET.get("top_ups"))
        return render(
            request,
            "user_home.html",
            {
                "user_info": user,
                "top_ups": top_up_page,
                "sales": sales_page,
                "form": TopUpForm,
                "transaction": transaction,
                "PaymentStatus": PaymentStatus,
            },
        )


def login(request):
    return render(request, "login.html")


@dashboard_admin
def products(request):
    if request.POST:
        product = ProductForm(request.POST, request.FILES)

        if "edit" in request.GET and request.GET["edit"] != "0":
            instance = Product.objects.get(id=request.GET["edit"])
            product = ProductForm(request.POST, request.FILES, instance=instance)

        if product.is_valid():
            product.category = Category.objects.get(
                name=product.cleaned_data["category"]
            )
            product.save()
            return HttpResponseRedirect("/products")

    product, product_sales = None, None
    pf = ProductForm
    if request.GET:
        if "edit" in request.GET and request.GET["edit"] != "0":
            product = Product.objects.get(id=request.GET["edit"])
            pf = ProductForm(instance=product)
        if "sales" in request.GET and request.GET["sales"] != "0":
            product = Product.objects.get(id=request.GET["sales"])
            transactions = ProductTransactions.objects.filter(product_id=product)
            product_sales = {
                "all": transactions,
                "sum": transactions.values("product_price").annotate(sum=Sum("amount")),
            }

    products = Product.objects.all().order_by("name")
    categories = Category.objects.all()
    return render(
        request,
        "products.html",
        {
            "products": products,
            "categories": categories,
            "product_form": pf,
            "current_product": product,
            "product_sales": product_sales,
        },
    )


@dashboard_admin
def delete(request):
    id = request.POST.dict()["id"]
    Product.objects.get(id=id).delete()
    return JsonResponse({"msg": f"Deleted product with {id}"})


@dashboard_admin
def toggle(request):
    id = request.POST.dict()["id"]
    product = Product.objects.get(id=id)
    product.enabled = not product.enabled
    product.save()
    return JsonResponse(
        {"msg": f"Set the state of product {id} to enabled={product.enabled}"}
    )


@dashboard_admin
def users(request, user_id=None):
    user, cards = None, None
    if user_id:
        user = User.objects.get(id=user_id)
        top_ups = TopUpTransaction.objects.all().filter(user_id=user)
        product_sales = list(
            ProductTransactions.objects.all().filter(transaction_id__user_id=user)
        )
        product_sale_groups = []
        for designation, member_group in groupby(
            product_sales, lambda sale: sale.transaction_id
        ):
            product_sale_groups.append(
                {"key": designation, "values": list(member_group)}
            )

        cards = []
        for i, card in enumerate(Card.objects.all().filter(user_id=user.id)):
            cards.append({"info": card})
            if card.active is False:
                cards[i]["token"] = CardConfirmation.objects.get(card=card).token

        top_up_page = create_paginator(top_ups, request.GET.get("top_ups"))
        sales_page = create_paginator(product_sale_groups, request.GET.get("sales"))

        return render(
            request,
            "user.html",
            {
                "user_info": user,
                "cards": cards,
                "top_ups": top_up_page,
                "sales": sales_page,
                "top_types": top_up_types,
            },
        )
    else:
        users = User.objects.all()

        # Only filter on user name if a name is given
        if request.GET.get("name"):
            users = users.filter(name__icontains=request.GET.get("name"))

        user_page = create_paginator(users, request.GET.get("users"), p_len=15)
        return render(request, "user.html", {"users": users, "user_page": user_page})


@dashboard_admin
def settings_page(request):
    vat = VAT.objects.all()
    categories = Category.objects.all()
    configuration = Configuration.objects.get(pk=1)
    return render(
        request,
        "settings.html",
        {"vat": vat, "categories": categories, "configuration": configuration},
    )


@dashboard_admin
def category(request):
    try:
        categories = json.loads(request.POST.dict()["categories"])
        for category in categories:
            if category["id"] == "0":
                cat = Category.objects.create(
                    name=category["name"], alcoholic=category["checked"]
                )
                cat.save()
            elif "delete" in category and category["delete"] is True:
                cat = Category.objects.get(id=category["id"])
                cat.delete()
            else:
                cat = Category.objects.get(id=category["id"])
                cat.name = category["name"]
                cat.alcoholic = category["checked"]
                cat.save()

        return JsonResponse({"msg": "Updated the mongoose categories"})
    except Exception as e:
        print(e)
        return JsonResponse(
            {"msg": "Something went wrong whilst trying to save the categories"},
            status=400,
        )


@dashboard_admin
def vat(request):
    try:
        vatBody = json.loads(request.POST.dict()["vat"])
        for vat in vatBody:
            if vat["id"] == "0":
                newVAT = VAT.objects.create(percentage=vat["percentage"])
                newVAT.save()
            elif "delete" in vat and vat["delete"] is True:
                delVAT = VAT.objects.get(id=vat["id"])
                delVAT.delete()
            else:
                newVAT = VAT.objects.get(id=vat["id"])
                newVAT.percentage = vat["percentage"]
                newVAT.save()

        return JsonResponse({"msg": "Updated the mongoose VAT percentages"})
    except Exception as e:
        print(e)
        return JsonResponse(
            {"msg": "Something went wrong whilst trying to save the VAT percentages"},
            status=400,
        )


@dashboard_admin
def settings_update(request):
    """
    Updates the configuration settings for the undead-mongoose application.

    Args:
        request (HttpRequest): The HTTP request object containing the updated configuration settings.

    Returns:
        JsonResponse: A JSON response indicating whether the configuration settings were successfully updated or not.
    """
    try:
        configuration = Configuration.objects.get(pk=1)
        settings = json.loads(request.POST.dict()["settings"])
        configuration.alc_time = settings["alc_time"]
        configuration.save()
        return JsonResponse({"msg": "Updated the mongoose configuration"})
    except Exception as e:
        print(e)
        return JsonResponse(
            {"msg": "Something went wrong whilst trying to save the configuration"},
            status=400,
        )


@dashboard_admin
def transactions(request):
    # Get product sale groups
    product_sales = ProductTransactions.objects.all()
    product_sales_sorted = sorted(
        product_sales, key=lambda sale: sale.transaction_id.date, reverse=True
    )
    product_sale_groups = []
    for designation, member_group in groupby(
        product_sales_sorted, lambda sale: sale.transaction_id
    ):
        product_sale_groups.append({"key": designation, "values": list(member_group)})

    # Get paginators
    top_up_page = create_paginator(
        TopUpTransaction.objects.all(), request.GET.get("top_ups")
    )
    sales_page = create_paginator(
        product_sale_groups, request.GET.get("sales"), p_len=10
    )
    ideal_page = create_paginator(
        IDealTransaction.objects.filter(added=True), request.GET.get("ideal"), p_len=10
    )

    return render(
        request,
        "transactions.html",
        {
            "top_ups": top_up_page,
            "sales": sales_page,
            "ideal": ideal_page,
            "last_week": timezone.now() - timedelta(weeks=1),
            "this_week": timezone.now(),
        },
    )


@dashboard_admin
def export_sale_transactions(request):
    """
    Exports the sale transactions in the given date range to a csv file.

    Args:
        request (HttpRequest): The HTTP request object containing the date range.

    Returns:
        HttpResponse: The csv file containing the sale transactions in the given date range.
    """
    try:
        req_get = request.GET
        export_type = req_get.get("type")
        start_date = req_get.get("start_date")
        end_date = req_get.get("end_date")
        if export_type == "mollie":
            if not start_date or not end_date:
                return HttpResponse("No date range given.", status=400)

            # Get the date range from the request
            current_date = timezone.now().strftime("%Y-%m-%d")

            # Get the transactions in the date range
            top_up_range = TopUpTransaction.objects.filter(
                date__range=[start_date, end_date], type=3
            ).all()
            ideal_transactions = IDealTransaction.objects.filter(
                date__range=[start_date, end_date]
            ).all()

            # Setup the export "csv"
            response_string = f"Factuurdatum,{current_date},ideal - {start_date} / {end_date},02,473\n"

            # Add the transactions to the export "csv"
            for t in top_up_range:
                response_string += (
                    f'"",8002,Mongoose - {t.id},9,{t.transaction_sum},""\n'
                )

            for t in ideal_transactions:
                response_string += (
                    f'"",8002,Mongoose - {t.transaction_id},9,{t.transaction_sum},""\n'
                )

            # Return the export "csv"
            return HttpResponse(response_string, content_type="text/csv")
        elif export_type == "pin":
            if not start_date or not end_date:
                return HttpResponse("No date range given.", status=400)

            # Get the date range from the request
            current_date = timezone.now().strftime("%Y-%m-%d")

            # Get the transactions in the date range
            if start_date and end_date:
                top_up_range = TopUpTransaction.objects.filter(
                    date__range=[start_date, end_date], type=1
                ).all()
            else:
                top_up_range = TopUpTransaction.objects.filter(
                    date=current_date, type=1
                ).all()

            # Turn transaction result into JSON
            json_resp = json.dumps(
                [
                    {
                        "member_id": t.user_id.id,
                        "name": t.user_id.name,
                        "price": float(t.transaction_sum),
                        "date": t.date.strftime("%Y-%m-%d"),
                    }
                    for t in top_up_range
                ]
            )

            # Return the created json
            return HttpResponse(json_resp, content_type="application/json")
        else:
            return HttpResponse("Export type not found", status=400)
    except Exception as e:
        print(e)
        return HttpResponse(
            "Something went wrong whilst trying to export the sale transactions.",
            status=400,
        )
