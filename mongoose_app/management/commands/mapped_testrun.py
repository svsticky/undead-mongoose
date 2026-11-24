"""Test Mongoose Mapped with purchases rung up through the real checkout API (/api/transaction),
spread over the current academic year.

  manage.py mapped_testrun               fake member; writes mapped_testrun.html to open in a browser
                                         while the dev server runs (no Keycloak login needed)
  manage.py mapped_testrun --user <id>   adds the purchases to an existing member (their Keycloak id,
                                         paid from their balance); log in as them and open /mapped
"""
import random
import string
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.test import Client
from django.utils import timezone

from admin_board_view.views import mapped_period, mapped_stats
from mongoose_app.keycloak import _keycloak_user_cache_key
from mongoose_app.models import Card, Category, Product, SaleTransaction, User, VAT

TEST_MEMBER = "mapped-test-member"


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("--user", help="Keycloak id of an existing member to add the purchases to")
        parser.add_argument("--purchases", type=int, default=40)

    def handle(self, *args, **options):
        if options["user"]:
            member = User.objects.filter(user_id=options["user"]).first()
            if not member:
                raise CommandError(f"No member with user_id {options['user']}; log in as them once first.")
        else:
            SaleTransaction.objects.filter(user_id__user_id=TEST_MEMBER).delete()  # from a previous run
            User.objects.filter(user_id=TEST_MEMBER).delete()
            member = User.objects.create(user_id=TEST_MEMBER, balance=Decimal("1000.00"))

        products = list(Product.objects.filter(enabled=True)) or self.create_products()

        # A temporary card, so purchases go through the checkout API exactly like the terminal does
        card = Card.objects.create(card_id="".join(random.choices(string.ascii_uppercase, k=8)), active=True, user_id=member)
        host = next((h for h in settings.ALLOWED_HOSTS if h and h != "*"), "localhost")
        client = Client(HTTP_HOST=host)
        since, _ = mapped_period()
        days = max((timezone.localdate() - since).days, 1)
        bought, failed = [], 0
        try:
            for _ in range(options["purchases"]):
                items = {p.id: random.randint(1, 3) for p in random.sample(products, k=min(len(products), random.randint(1, 2)))}
                response = client.post(
                    "/api/transaction", content_type="application/json", HTTP_AUTHORIZATION=settings.API_TOKEN,
                    data={"uuid": card.card_id, "items": [{"id": i, "amount": a} for i, a in items.items()]},
                )
                if response.status_code != 201:
                    failed += 1
                    continue
                # The API stamps "now"; spread the purchases back over this academic year
                sale = SaleTransaction.objects.filter(user_id=member).latest("id")
                moment = timezone.now() - timedelta(days=random.randrange(days), hours=random.randrange(8))
                SaleTransaction.objects.filter(id=sale.id).update(date=moment)
                bought.append(items)
        finally:
            card.delete()

        items = sum(a for b in bought for a in b.values())
        self.stdout.write(self.style.SUCCESS(
            f"Rang up {len(bought)} purchases ({items} items) through /api/transaction since {since}."))
        if failed:
            self.stdout.write(self.style.WARNING(f"{failed} purchases failed (not enough balance?)."))

        if options["user"]:
            self.stdout.write("Now log in as that member and open /mapped (outside the window only board members can).")
            return

        # Render the real page for the fake member. Its name can't come from Keycloak, so cache one.
        cache.set(_keycloak_user_cache_key(TEST_MEMBER), {"firstName": "Test", "lastName": "Member"})
        html = render_to_string("mapped.html", {"user_info": member, **mapped_stats(member)})
        html = html.replace("<head>", f'<head>\n  <base href="{settings.BASE_URL or "http://localhost:8000"}/">', 1)
        with open("mapped_testrun.html", "w") as f:
            f.write(html)
        self.stdout.write("Wrote mapped_testrun.html: open it in your browser while the dev server is running.")

    def create_products(self):
        vat = VAT.objects.first() or VAT.objects.create(percentage=9)
        fris = Category.objects.create(name="Fris")
        bier = Category.objects.create(name="Bier", alcoholic=True)
        return [
            Product.objects.create(name=name, category=category, price=Decimal(price), vat=vat)
            for name, category, price in [("Cola", fris, "1.00"), ("Fanta", fris, "1.00"), ("Hertog Jan", bier, "1.20")]
        ]
