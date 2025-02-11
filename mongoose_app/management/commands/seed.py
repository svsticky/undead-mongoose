from django.core.management.base import BaseCommand
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
        confirmation_id = 0
        for user in users:
            num_cards = randint(0, 2)
            for _ in range(num_cards):
                active = randint(0, 9) == 0
                card = Card(card_id, faker.ean(length=8), active, user.id)
                card.save()
                card_id += 1

                if active:
                    three_years_ago = datetime.now() - timedelta(days=3 * 365)
                    date = faker.date_time_between(three_years_ago)
                    confirmation = CardConfirmation(
                        confirmation_id, date, card.id, faker.password(length=32)
                    )
                    confirmation.save()
                    confirmation_id += 1

        print(f"Created {card_id} Cards")

        # TopUp- and IDealTransactions
        topup_trans_id = 0
        trans_count = 0
        for user in users:
            num_transactions = randint(10, 20)
            trans_count += num_transactions
            for _ in range(num_transactions):
                price = randprice(5, 100)
                is_topup = randint(0, 5) == 0
                if is_topup:
                    topup = TopUpTransaction(
                        topup_trans_id, user.id, price, datetime.now(), False, 1
                    )
                    topup.save()
                    topup_trans_id += 1
                else:
                    ideal = IDealTransaction(
                        user.id,
                        price,
                        datetime.now(),
                        faker.uuid4(cast_to=None),
                        faker.enum(PaymentStatus),
                        False,
                    )
                    ideal.save()

        print(f"Created {trans_count} TopUp- and IDealTransactions")

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

        # Sale- and ProductTransactions
        prod_trans_id = 0
        for sale_trans_id in range(0, 200):
            cancelled = randint(0, 50) == 0
            user = randelem(users)
            product = randelem(products)
            amount = randint(1, 8)
            three_years_ago = datetime.now() - timedelta(days=3 * 365)
            date = faker.date_time_between(three_years_ago)
            sale_trans = SaleTransaction(
                sale_trans_id,
                user.id,
                amount * product.price,
                date,
                cancelled,
                cancelled,
            )
            sale_trans.save()
            if not cancelled:
                prod_trans = ProductTransactions(
                    prod_trans_id,
                    product.id,
                    sale_trans_id,
                    product.price,
                    product.vat.percentage,
                    amount,
                )
                prod_trans_id += 1
                prod_trans.save()

        print(f"Created {prod_trans_id} Sale- and ProductTransactions")


def randprice(start, end):
    euros = randint(start, end - 1)
    cents = randint(0, 99)
    return Decimal(f"{euros}.{cents}")


def randelem(l):
    index = randint(0, len(l) - 1)
    return l[index]
