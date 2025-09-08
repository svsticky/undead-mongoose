from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware
from datetime import datetime, timedelta
from random import randint, seed as randseed
from faker import Faker
from faker.providers import misc, color, company, person, barcode
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
        for provider in [misc, color, company, person, barcode]:
            faker.add_provider(provider)
        if seed:
            faker.seed_instance(seed)
            randseed(seed)

        # Configuration
        Configuration().save()

        print("Created 1 Configuration")

        # Users
        users = [
            User(
                user_id,
                user_id,
                faker.name(),
                faker.date_of_birth(minimum_age=15, maximum_age=28),
                faker.email(),
                Decimal(0),
            )
            for user_id in range(20)
        ]
        for user in users:
            user.save()

        test_user = randelem(users)
        test_user.email = "test@svsticky.nl"
        test_user.save()

        print(f"Created {len(users)} Users")

        # Cards and CardConfirmations
        card_id = 0
        cards = []
        confirms = []
        confirmation_id = 0
        for user in users:
            chance = randint(1, 10)
            if chance <= 1:
                num_cards = 0
            elif chance <= 8:
                num_cards = 1
            else:
                num_cards = 2

            for _ in range(num_cards):
                active = randint(0, 9) != 0
                card = Card(card_id, faker.ean(length=8), None, active, user.id)
                card.save()
                cards.append(card)
                card_id += 1

                if active:
                    three_years_ago = datetime.now() - timedelta(days=3 * 365)
                    date = make_aware(faker.date_time_between(three_years_ago))
                    confirmation = CardConfirmation(
                        confirmation_id, date, card.id, faker.password(length=32)
                    )
                    confirmation.save()
                    confirmation_id += 1
                    confirms.append(confirmation)

        print(f"Created {card_id} Cards")

        # Categories
        num_nonalcoholic_categories = randint(3, 6)
        categories = [
            Category(id, faker.unique.color_name(), False)
            for id in range(0, num_nonalcoholic_categories)
        ]
        categories.append(
            Category(num_nonalcoholic_categories, faker.unique.color_name(), True)
        )
        for category in categories:
            category.save()

        print(f"Created {len(categories)} Categories")

        # VATs
        vats = [VAT(id, randint(0, 100)) for id in range(0, 2)]
        for vat in vats:
            vat.save()

        print(f"Created {len(vats)} VATs")

        # Products
        products = []
        for id in range(0, 30):
            price = randprice(0, 10)
            category = randelem(categories)
            vat = randelem(vats)
            enabled = randint(0, 10) > 3
            product = Product(
                id, faker.catch_phrase(), price, None, category.id, vat.id, enabled
            )
            product.save()
            products.append(product)

        print(f"Created {len(products)} Products")

        # TopUp- and IDealTransactions
        topup_trans_id = 0
        trans_count = 0
        prod_trans_id = 0
        sale_trans_id = 0
        for user in users:
            if not any(
                card.user_id.user_id == user.id and card.active for card in cards
            ):
                continue

            num_transactions = randint(10, 20)
            trans_count += num_transactions

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
                    topup = TopUpTransaction(
                        topup_trans_id, user.id, topup_price, start_date, False, 1
                    )
                    topup.save()
                    topup_trans_id += 1
                else:
                    ideal = IDealTransaction(
                        user.id,
                        topup_price,
                        make_aware(faker.date_time_between(end_date - timedelta(days=3 * 365), end_date)),
                        faker.uuid4(cast_to=None),
                        PaymentStatus.PAID,
                        False,
                    )
                    ideal.save()

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

                    sale_trans = SaleTransaction(
                        sale_trans_id,
                        user.id,
                        trans_total,
                        make_aware(faker.date_time_between(end_date - timedelta(days=3 * 365), end_date)),
                        False,
                        False,
                    )
                    sale_trans.save()
                    sale_trans_id += 1

                    # Products in the cart are evenly divided into sale transactions
                    for amount, product in cart_slice:
                        prod_trans = ProductTransactions(
                            prod_trans_id,
                            product.id,
                            sale_trans.id,
                            product.price,
                            product.vat.percentage,
                            amount,
                        )
                        prod_trans_id += 1
                        prod_trans.save()

                cart_total = sum(amount * product.price for amount, product in cart)
                print(
                    f"Created {num_sale_trans} SaleTransaction and {len(cart)} ProductTransactions totalling €{cart_total}"
                )

        print(f"Created {trans_count} TopUp- and IDealTransactions")
        print(f"Created {prod_trans_id} Sale- and ProductTransactions")


def randprice(start, end):
    euros = randint(start, end - 1)
    cents = randint(0, 99)
    return Decimal(f"{euros}.{cents}")


def randelem(l):
    index = randint(0, len(l) - 1)
    return l[index]
