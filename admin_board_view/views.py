import json
from operator import itemgetter
from django.db.models import Count, Sum
from django.db.models.functions import ExtractHour, ExtractWeekDay
from django.http.response import JsonResponse
from django.shortcuts import render, HttpResponseRedirect
from django.http import Http404, HttpResponse
from django.utils import timezone
from datetime import date, datetime, timedelta
from itertools import groupby

from admin_board_view.middleware import dashboard_authenticated, dashboard_admin
from admin_board_view.utils import create_paginator
from undead_mongoose.settings import TRANSACTION_FEE
from .models import *
from mollie.api.client import Client
from django.conf import settings
from .forms import TopUpForm
from mongoose_app.keycloak import search_keycloak_users, cache_keycloak_user


def get_user_home_context(request):
    try:
        user = User.objects.get(user_id=request.user.username)
    except User.DoesNotExist:
        user = None

    if user:
        # Get product sales
        product_sales = list(
            ProductTransactions.objects.all().filter(transaction_id__user_id=user)
        )
        product_sale_groups = []
        for designation, member_group in groupby(
            product_sales, lambda sale: sale.transaction_id
        ):
            member_list = list(member_group)
            product_sale_groups.append(
                {
                    "key": designation,
                    "date": member_list[0].transaction_id.date,
                    "values": member_list,
                }
            )
        product_sale_groups.sort(key=itemgetter("date"), reverse=True)
        sales_page = create_paginator(product_sale_groups, request.GET.get("sales"))

        # Get topup page
        top_ups = (
            TopUpTransaction.objects.all()
            .filter(user_id=user)
            .values_list("date", "transaction_sum")
        )
        ideal_transactions = (
            IDealTransaction.objects.all()
            .filter(user_id=user, added=True)
            .values_list("date", "transaction_sum")
        )
        all_top_ups = sorted(
            [(d, t, "Pin") for d, t in top_ups]
            + [(d, t, "iDeal") for d, t in ideal_transactions],
            key=lambda transaction: transaction[0], reverse=True
        )
        top_up_page = create_paginator(all_top_ups, request.GET.get("top_ups"))
        cards = Card.objects.filter(user_id__pk=user.pk)
    else:
        sales_page = create_paginator([], request.GET.get("sales"))
        top_up_page = create_paginator([], request.GET.get("top_ups"))
        cards = []

    transaction_id = request.GET.dict().get("transaction_id")
    transaction = (
        IDealTransaction.objects.get(transaction_id=transaction_id)
        if transaction_id
        else None
    )

    return {
        "user_info": user,
        "top_ups": top_up_page,
        "sales": sales_page,
        "form": TopUpForm,
        "transaction": transaction,
        "PaymentStatus": PaymentStatus,
        "TRANSACTION_FEE": settings.TRANSACTION_FEE,
        "error": request.GET.get("error"),
        "cards": cards,
        "mapped_open": mapped_open(),
    }


def mapped_window():
    """(month, day) of the yearly Mongoose Mapped start and end, as set by the board (default: June).
    Only month/day count, so the board's dates keep working in later years."""
    config = Configuration.objects.first()
    start = (config and config.mapped_start) or date(2000, 6, 1)
    end = (config and config.mapped_end) or date(2000, 6, 30)
    return (start.month, start.day), (end.month, end.day)


def mapped_open(today=None):
    today = today or timezone.localdate()
    start, end = mapped_window()
    return start <= (today.month, today.day) <= end


def mapped_period(today=None):
    """[since, until) of the academic year belonging to the most recent Mapped window, so outside
    the window (e.g. a board preview in October) it shows the year that was recapped, not the
    first weeks of the new one."""
    today = today or timezone.localdate()
    start, _ = mapped_window()
    end_year = today.year if (today.month, today.day) >= start else today.year - 1
    return date(end_year - 1, 9, 1), date(end_year, 9, 1)


def mapped_stats(user, today=None):
    """Purchase stats for `user` over the academic year given by mapped_period."""
    since, until = mapped_period(today)
    sales = SaleTransaction.objects.filter(
        user_id=user, cancelled=False, date__date__gte=since, date__date__lt=until
    )
    products = ProductTransactions.objects.filter(transaction_id__in=sales)

    def top(qs, field, n=1):
        return list(qs.values(field).annotate(total=Count("id")).order_by("-total")[:n])

    weekday = top(sales.annotate(day=ExtractWeekDay("date")), "day")
    hour = top(sales.annotate(hour=ExtractHour("date")), "hour")
    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    items = products.aggregate(s=Sum("amount"))["s"] or 0
    alcoholic = products.filter(product_id__category__alcoholic=True).aggregate(s=Sum("amount"))["s"] or 0
    ideal_topups = IDealTransaction.objects.filter(
        user_id=user, status=PaymentStatus.PAID, date__date__gte=since, date__date__lt=until
    ).count()
    return {
        "since": since,
        "until": until,
        "visits": sales.count(),
        "spent": sales.aggregate(s=Sum("transaction_sum"))["s"] or 0,
        "items": items,
        "alcohol_pct": round(100 * alcoholic / items) if items else 0,
        "ideal_topups": ideal_topups,
        "ideal_fees": ideal_topups * settings.TRANSACTION_FEE,
        "top_products": products.values("product_id__name", "product_id__image")
            .annotate(total=Sum("amount")).order_by("-total")[:5],
        "top_category": products.values("product_id__category__name")
            .annotate(total=Sum("amount")).order_by("-total").first(),
        "weekday": days[weekday[0]["day"] - 1] if weekday else None,
        "hour": hour[0]["hour"] if hour else None,
    }


@dashboard_authenticated
def mapped(request):
    # Only ever the logged-in user's own data; board members may preview outside the window.
    if not (mapped_open() or request.user.is_superuser):
        return HttpResponseRedirect("/")
    user = User.objects.filter(user_id=request.user.username).first()
    if not user:
        return HttpResponseRedirect("/")
    return render(request, "mapped.html", {"user_info": user, **mapped_stats(user)})


def mapped_demo(request):
    """Mapped with fake data, for working on the design locally. Only exists when DEBUG is on."""
    if not settings.DEBUG:
        raise Http404
    products = [("Cola Zero", 61), ("Mars", 40), ("Tosti", 22), ("Fanta Cassis", 18), ("Twix", 9)]
    since, until = mapped_period()
    return render(request, "mapped.html", {
        "user_info": {"name": "Demo"},
        "since": since,
        "until": until,
        "visits": 142,
        "items": 231,
        "spent": Decimal("187.40"),
        "top_products": [{"product_id__name": n, "total": t} for n, t in products],
        "top_category": {"product_id__category__name": "Fris", "total": 120},
        "weekday": "Thursday",
        "hour": 16,
        "alcohol_pct": 23,
        "ideal_topups": 7,
        "ideal_fees": 7 * settings.TRANSACTION_FEE,
    })


# @dashboard_authenticated
# def index(request):
#     return render(
#         request,
#         "user_home.html",
#         get_user_home_context(request),
#     )


@dashboard_authenticated
def index(request):
    context = get_user_home_context(request)

    if request.user.is_superuser:
        product_amount = Product.objects.count()
        total_balance = sum(user.balance for user in User.objects.all())
        product_sales = ProductTransactions.objects.prefetch_related('transaction_id').order_by('transaction_id__date').reverse()
        product_sale_groups = []
        for designation, member_group in groupby(product_sales, lambda sale: sale.transaction_id):
            product_sale_groups.append({"key": designation, "values": list(member_group)})

        context |= {
            "product_amount": product_amount,
            "recent_sales": product_sale_groups[:5],
            "total_balance": total_balance,
            "top_types": top_up_types,
        }

    return render(request, "home.html", context)


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

        top_ups = (
            TopUpTransaction.objects.all()
            .filter(user_id=user)
            .values_list("date", "transaction_sum")
        )
        ideal_transactions = (
            IDealTransaction.objects.all()
            .filter(user_id=user, added=True)
            .values_list("date", "transaction_sum")
        )
        all_top_ups = sorted(
            [(d, t, "Pin") for d, t in top_ups]
            + [(d, t, "iDeal") for d, t in ideal_transactions],
            key=lambda transaction: transaction[0],
        )
        top_up_page = create_paginator(all_top_ups, request.GET.get("top_ups"))
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
        name_query = request.GET.get("name")
        if name_query:
            try:
                profiles = search_keycloak_users(name_query)
            except Exception as e:
                print(e)
                profiles = []

            for profile in profiles:
                cache_keycloak_user(profile["id"], profile)

            users = list(
                User.objects.filter(user_id__in=[p["id"] for p in profiles]).order_by("id")
            )
        else:
            users = list(User.objects.all().order_by("id"))

        user_page = create_paginator(users, request.GET.get("users"), p_len=15)
        return render(request, "user.html", {"user_page": user_page})


@dashboard_admin
def user_search(request):
    """
    Bounded autocomplete for the "Find user" / "Add balance to user" inputs:
    resolves Keycloak profiles only for users matching what was typed, so
    it stays cheap regardless of how many members are registered.
    """
    term = request.GET.get("q", "").strip()
    if not term:
        return JsonResponse({"results": []})

    try:
        profiles = search_keycloak_users(term)
    except Exception as e:
        print(e)
        return JsonResponse({"results": []})

    local_users = {
        u.user_id: u
        for u in User.objects.filter(user_id__in=[p["id"] for p in profiles])
    }

    results = []
    for profile in profiles:
        user = local_users.get(profile["id"])
        if not user:
            continue
        cache_keycloak_user(user.user_id, profile)
        results.append({"id": user.id, "user_id": user.user_id, "name": user.name})

    return JsonResponse({"results": results})


@dashboard_admin
def settings_page(request):
    vat = VAT.objects.all()
    categories = list(Category.objects.all())
    categories.sort(key=lambda cat: cat.order)

    configuration = Configuration.objects.all()[0]
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

            if category.get("delete"):
                cat = Category.objects.get(id=category["id"])
                cat.delete()
            elif category["id"] == "-1": # -1 signifies a new category
                cat = Category.objects.create(
                    name=category["name"], alcoholic=category["checked"], order=category["order"]
                )
                cat.save()
            else:
                cat = Category.objects.get(id=category["id"])
                cat.name = category["name"]
                cat.alcoholic = category["checked"]
                cat.order = category["order"]
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
        configuration.mapped_start = settings.get("mapped_start")
        configuration.mapped_end = settings.get("mapped_end")
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
    product_sales = ProductTransactions.objects.prefetch_related('transaction_id').order_by('transaction_id__date').reverse()

    product_sale_groups = []
    for designation, member_group in groupby(product_sales, lambda sale: sale.transaction_id):
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
def salesInfo(request):
    today = timezone.now().date()
    default_from_date = today - timedelta(days=7)
    default_to_date = today

    from_date_str = request.GET.get('from_date', default_from_date.strftime('%Y-%m-%d'))
    to_date_str = request.GET.get('to_date', default_to_date.strftime('%Y-%m-%d'))

    # Ensure the dates are timezone-aware
    # Cap date at '9999-12-31'
    from_date = timezone.make_aware(datetime.strptime(from_date_str if int(from_date_str.split('-')[0]) <= 9999 else '9999-12-31', '%Y-%m-%d'))
    to_date = timezone.make_aware(datetime.strptime(to_date_str if int(to_date_str.split('-')[0]) <= 9999 else '9999-12-31','%Y-%m-%d'))

    sort_order = request.GET.get('sort_order', 'descending')
    ordering = 'total_amount' if sort_order == 'ascending' else '-total_amount'

    product_stats = ProductTransactions.objects.filter(
        transaction_id__date__gte=from_date,
        transaction_id__date__lte=to_date,
        transaction_id__cancelled=False
    ).values('product_id_id', 'product_id__name').annotate(
        total_amount=Sum('amount')
    ).order_by(ordering)

    context = {
        'productStats': product_stats,
        'from_date': from_date,
        'to_date': to_date,
        'sort_order': sort_order,
        'toggle_order': 'ascending' if sort_order == 'descending' else 'descending',
        'last_week': default_from_date,
        'this_week': default_to_date,
    }

    return render(request, 'product_sales_info.html', context)


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
        response_type = req_get.get("response_type")

        # Get the date range from the request
        current_date = timezone.now().strftime("%Y-%m-%d %H:%M:%S")

        # Select the relevant data
        if export_type == "mollie":
            # Require both start and end date
            if not start_date or not end_date:
                return HttpResponse("No date range given.", status=400)

            data = IDealTransaction.objects.filter(
                date__range=[start_date, end_date], status=PaymentStatus.PAID
            ).all()
        elif export_type == "pin":
            # Require either dates or just one
            if start_date and end_date:
                data = TopUpTransaction.objects.filter(
                    date__range=[start_date, end_date], type=1
                ).all()
            else:
                data = TopUpTransaction.objects.filter(date=current_date, type=1).all()
        else:
            return HttpResponse(f"Invalid export type {export_type}", status=400)

        # Create the response in the requested format
        if response_type == "csv":
            response_string = f"Factuurdatum,{current_date},{export_type} - {start_date} / {end_date},02,473\n"

            # Add the transactions to the export "csv"
            for t in data:
                name = (
                    "pin betaling"
                    if export_type == "pin"
                    else f"topup {t.user_id.name}"
                )
                response_string += f'"",08030,Mongoose - {name},0,{"{:.2f}".format(t.transaction_sum)},""\n'

            # Add transaction fee row mollie payments
            if export_type == "mollie":
                t_count = len(data)
                response_string += f'"",5007,Mongoose transaction fee {settings.TRANSACTION_FEE:.2f} x {t_count},21,{t_count * settings.TRANSACTION_FEE:.2f},TRX\n'

            # Return the export "csv"
            return HttpResponse(response_string, content_type="text/csv")
        elif response_type == "json":
            json_resp = json.dumps(
                [
                    {
                        "member_id": t.user_id.id,
                        "name": t.user_id.name,
                        "price": "{:.2f}".format(t.transaction_sum),
                        "date": t.date.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    for t in data
                ]
            )

            return HttpResponse(json_resp, content_type="application/json")
        else:
            return HttpResponse(f"Invalid response type {response_type}", status=400)
    except Exception as e:
        print(e)
        return HttpResponse(
            "Something went wrong whilst trying to export the sale transactions.",
            status=400,
        )
