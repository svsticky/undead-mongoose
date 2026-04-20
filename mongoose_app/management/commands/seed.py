from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware
from datetime import datetime, timedelta
from random import randint, seed as randseed
from faker import Faker
from faker.providers import misc, color, company, person, barcode, DynamicProvider
from decimal import Decimal
from mongoose_app.models import (
    Configuration,
    User,
    Card,
    CardConfirmation,
    TopUpTransaction,
    IDealTransaction,
    SaleTransaction,
    ProductTransactions,
    Product,
    Category,
    VAT,
    PaymentStatus,
)


class Command(BaseCommand):
    help = "Seed the database"
    requires_migration_checks = True

    def add_arguments(self, parser):
        parser.add_argument(
            "--seed", type=int, help="Seed for the faker instance to use"
        )

    def handle(self, *args, **options):
        self.remove_data()
        self.seed(options["seed"])

    def remove_data(self):
        models = [
            Configuration,
            User,
            Card,
            CardConfirmation,
            TopUpTransaction,
            IDealTransaction,
            SaleTransaction,
            ProductTransactions,
            Product,
            Category,
            VAT,
        ]
        for model in models:
            model.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Removed all model records"))

    def seed(self, seed):
        def print(s):
            self.stdout.write(self.style.SUCCESS(s))

        faker = Faker("nl_NL")
        card_names_provider = DynamicProvider(
            provider_name="card_name",
            elements=["OV-Chipkaart","Bestuur Bankpas","UU Medewerkerspas","Chipsoft waterfles"]
        )
        for provider in [misc, color, company, person, barcode, card_names_provider]:
            faker.add_provider(provider)
        if seed:
            faker.seed_instance(seed)
            randseed(seed)

        # Users
        users = []
        for id in range(20):
            user = User.objects.create(
                user_id=id,
                name=faker.name(),
                birthday=faker.date_of_birth(minimum_age=15, maximum_age=28),
                email=faker.email(),
                balance=Decimal(0)
            )
            users.append(user)
                

        test_user = randelem(users)
        test_user.email = "test@svsticky.nl"
        test_user.save()

        print(f"Created {len(users)} Users")

        # Cards and CardConfirmations
        cards = []
        confirms = []
        for user in users:
            chance = randint(1, 10)
            if chance <= 1:
                num_cards = 0
            elif chance <= 8:
                num_cards = 1
            else:
                num_cards = 2

            for _ in range(num_cards):
                active = randint(1, 10) != 0
                name = faker.card_name()

                card = Card.objects.create(
                    card_id=faker.ean(length=8),
                    card_name=name,
                    active=active,
                    user_id=user
                )
                cards.append(card)

                if active:
                    three_years_ago = datetime.now() - timedelta(days=3 * 365)
                    activation_date = make_aware(faker.date_time_between(three_years_ago))
                    card.last_used = make_aware(faker.date_time_between(activation_date))
                    card.save()

                confirmation = CardConfirmation.objects.create(
                    timestamp=activation_date,
                    card_id=card.id,
                    token=faker.password(length=32)
                )
                confirms.append(confirmation)

        print(f"Created {len(cards)} Cards")

        # Categories
        category_count = randint(3,6)
        categories = []
        for i in range(category_count):
            cat = Category.objects.create(
                name=faker.unique.color_name(),
                alcoholic=(i==0),
                order=i
            )
            categories.append(cat)

        print(f"Created {len(categories)} Categories")

        # VATs
        vats = []
        for id in range(3):
            vat = VAT.objects.create(percentage=randint(0,100))
            vats.append(vat)

        print(f"Created {len(vats)} VATs")

        # Products
        products = []
        for _ in range(30):
            enabled = randint(0, 10) > 3
            product = Product.objects.create(
                name=faker.catch_phrase(),
                price=randprice(0, 3),
                image=None,
                category=randelem(categories),
                vat=randelem(vats),
                enabled=enabled
            )
            product.save()
            products.append(product)

        print(f"Created {len(products)} Products")

        # TopUp- and IDealTransactions
        topup_trans_count = 0
        sale_trans_count = 0
        for user in users:
            if not any(
                card.user_id.user_id == user.id and card.active for card in cards
            ):
                continue

            num_transactions = randint(10, 20)
            topup_trans_count += num_transactions
            # First the earliest card confirmation that is linked to this user
            first_date = sorted(
                confirm.timestamp
                for confirm in confirms
                if confirm.card.user_id.user_id == user.id
            )[0]

            dates = sorted(
                [make_aware(faker.date_time_between(first_date)) for _ in range(num_transactions)]
            )

            balance = 0
            # Process the topup transactions in chronological order
            for start_date, end_date in zip(dates, [*dates[1:], datetime.now()]):
                # Create topup
                topup_price = randprice(5, 100)
                balance += topup_price
                is_topup = randint(0, 5) == 0
                if is_topup:
                    TopUpTransaction.objects.create(
                        user_id=user,
                        transaction_sum=topup_price,
                        type=1
                    )
                else:
                    IDealTransaction.objects.create(
                        transaction_sum=topup_price,
                        date=make_aware(faker.date_time_between(end_date - timedelta(days=3 * 365), end_date)),
                        user_id=user,
                        status=PaymentStatus.PAID,
                        added=False
                    )

                trans_text = "Topup" if is_topup else "iDeal"
                print(f"Created {trans_text} transaction for €{topup_price}")

                # Then spend the money from the topup
                cart = []
                while True:
                    amount = randint(1, 3)
                    product = randelem(products)
                    if amount * product.price > balance:
                        if len(cart) == 0:
                            # We need at least one product transaction per sale transaction
                            continue
                        else:
                            break

                    balance -= amount * product.price
                    cart.append((amount, product))

                # Divide the cart into some sale transactions, at most 3 if the cart is big enough
                num_sale_trans = randint(1, min(3, len(cart)))
                for i in range(num_sale_trans):
                    start_index = int(i * len(cart) / num_sale_trans)
                    end_index = int((i + 1) * len(cart) / num_sale_trans)

                    cart_slice = cart[start_index:end_index]
                    trans_total = sum(
                        amount * product.price for amount, product in cart_slice
                    )

                    sale_trans = SaleTransaction.objects.create(
                        user_id=user,
                        transaction_sum=trans_total,
                        date=make_aware(faker.date_time_between(end_date - timedelta(days=3 * 365), end_date)),
                        cancelled=False,
                        added=False,
                    )

                    # Products in the cart are evenly divided into sale transactions
                    for amount, product in cart_slice:
                        ProductTransactions.objects.create(
                            product_id=product,
                            transaction_id=sale_trans,
                            product_price=product.price,
                            product_vat=product.vat.percentage,
                            amount=amount,
                        )
                        sale_trans_count += 1

                cart_total = sum(amount * product.price for amount, product in cart)
                print(f"Created {num_sale_trans} SaleTransactions and {len(cart)} ProductTransactions totalling €{cart_total}")

        print(f"Created {topup_trans_count} TopUp- and IDealTransactions")
        print(f"Created {sale_trans_count} Sale- and ProductTransactions")


def randprice(start, end):
    euros = randint(start, end - 1)
    cents = randint(0, 99)
    return Decimal(f"{euros}.{cents}")


def randelem(l):
    index = randint(0, len(l) - 1)
    return l[index]
