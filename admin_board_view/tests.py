from decimal import Decimal
from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from mongoose_app.models import User as MongooseUser, Product, Category, VAT

AuthUser = get_user_model()

# name/birthday/email come from Keycloak now, keyed by user_id -- stand in
# for that with a fake profile per test account instead of a real lookup.
KEYCLOAK_PROFILES = {
    "normal@example.com": {"firstName": "Normal", "lastName": "User", "email": "normal@example.com"},
    "admin@example.com": {"firstName": "Admin", "lastName": "User", "email": "admin@example.com"},
}

class AdminBoardViewTests(TestCase):
    def setUp(self):
        keycloak_patcher = patch(
            "mongoose_app.models.get_cached_keycloak_user",
            side_effect=lambda user_id: KEYCLOAK_PROFILES.get(user_id),
        )
        self.addCleanup(keycloak_patcher.stop)
        keycloak_patcher.start()

        # Create test category and vat for product creation if needed
        self.category = Category.objects.create(name="Test Category", order=1)
        self.vat = VAT.objects.create(percentage=21)

        # Create normal user in auth and mongoose. user_id matches the auth
        # user's username, mirroring how OIDC login joins the two records.
        self.normal_auth_user = AuthUser.objects.create_user(
            username="normal@example.com",
            email="normal@example.com",
            password="password"
        )
        self.normal_mongoose_user = MongooseUser.objects.create(
            user_id="normal@example.com",
            balance=15.00
        )

        # Create admin user in auth and mongoose
        self.admin_auth_user = AuthUser.objects.create_superuser(
            username="admin@example.com",
            email="admin@example.com",
            password="password"
        )
        self.admin_mongoose_user = MongooseUser.objects.create(
            user_id="admin@example.com",
            balance=50.00
        )

        self.client = Client()

    def test_index_normal_user_sees_user_home(self):
        self.client.force_login(self.normal_auth_user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user_home.html")
        self.assertContains(response, "Normal User")

    def test_index_admin_user_sees_user_home(self):
        self.client.force_login(self.admin_auth_user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user_home.html")
        self.assertContains(response, "Admin User")

    def test_admin_dashboard_accessible_by_superuser(self):
        self.client.force_login(self.admin_auth_user)
        response = self.client.get("/admin_dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")
        self.assertContains(response, "Admin Dashboard")

    def test_admin_dashboard_denied_for_normal_user(self):
        self.client.force_login(self.normal_auth_user)
        response = self.client.get("/admin_dashboard")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login"))


class MappedTests(TestCase):
    def setUp(self):
        AdminBoardViewTests.setUp(self)
        from datetime import date, datetime
        from django.utils import timezone
        from mongoose_app.models import Configuration, SaleTransaction, ProductTransactions
        from admin_board_view import views
        self.views, self.date = views, date
        # Stats are evaluated as if it's mid-June 2027, i.e. for the 2026/27 academic year.
        self.today = date(2027, 6, 15)
        self.at = lambda *ymd: timezone.make_aware(datetime(*ymd, 12, 0))
        self.config = Configuration.objects.first()  # created by a migration
        cola = Product.objects.create(name="Cola", price=1, category=self.category, vat=self.vat)
        mars = Product.objects.create(name="Mars", price=1, category=self.category, vat=self.vat)
        for product, amount, cancelled in [(cola, 3, False), (mars, 1, False), (mars, 9, True)]:
            sale = SaleTransaction.objects.create(user_id=self.normal_mongoose_user, transaction_sum=amount,
                                                  cancelled=cancelled, date=self.at(2027, 3, 1))
            ProductTransactions.objects.create(product_id=product, transaction_id=sale, product_price=1, product_vat=21, amount=amount)

    def test_window_defaults_to_june(self):
        d = self.date
        self.assertTrue(self.views.mapped_open(d(2027, 6, 15)))
        self.assertFalse(self.views.mapped_open(d(2027, 7, 1)))

    def test_period_is_academic_year_of_latest_window(self):
        d, period = self.date, self.views.mapped_period
        self.assertEqual(period(d(2027, 6, 15)), (d(2026, 9, 1), d(2027, 9, 1)))
        # A preview in October still shows the year that was just recapped, not the new one
        self.assertEqual(period(d(2026, 10, 1)), (d(2025, 9, 1), d(2026, 9, 1)))
        self.assertEqual(period(d(2027, 5, 31)), (d(2025, 9, 1), d(2026, 9, 1)))
        # A window starting in May already covers the current year
        self.config.mapped_start = d(2027, 5, 20)
        self.config.save()
        self.assertEqual(period(d(2027, 5, 25)), (d(2026, 9, 1), d(2027, 9, 1)))

    def test_stats_only_count_purchases_in_period(self):
        from mongoose_app.models import SaleTransaction
        for ymd in [(2026, 8, 31), (2027, 9, 1)]:  # just before and just after 2026/27
            SaleTransaction.objects.create(user_id=self.normal_mongoose_user, transaction_sum=1, date=self.at(*ymd))
        self.assertEqual(self.views.mapped_stats(self.normal_mongoose_user, self.today)["visits"], 2)

    def test_stats_ignore_cancelled_sales(self):
        stats = self.views.mapped_stats(self.normal_mongoose_user, self.today)
        self.assertEqual(stats["visits"], 2)
        self.assertEqual(stats["items"], 4)
        self.assertEqual(stats["top_products"][0]["product_id__name"], "Cola")
        self.assertEqual(stats["alcohol_pct"], 0)
        self.assertEqual(stats["ideal_fees"], 0)

    def test_alcohol_and_ideal_fee_stats(self):
        from mongoose_app.models import Category, IDealTransaction, PaymentStatus, SaleTransaction, ProductTransactions
        beer = Product.objects.create(name="Beer", price=1, vat=self.vat,
                                      category=Category.objects.create(name="Bier", alcoholic=True))
        sale = SaleTransaction.objects.create(user_id=self.normal_mongoose_user, transaction_sum=4, date=self.at(2027, 3, 1))
        ProductTransactions.objects.create(product_id=beer, transaction_id=sale, product_price=1, product_vat=21, amount=4)
        for status in [PaymentStatus.PAID, PaymentStatus.PAID, PaymentStatus.CANCELLED]:
            IDealTransaction.objects.create(user_id=self.normal_mongoose_user, transaction_sum=10, status=status,
                                            date=self.at(2027, 3, 1))
        stats = self.views.mapped_stats(self.normal_mongoose_user, self.today)
        self.assertEqual(stats["alcohol_pct"], 50)  # 4 beers out of 8 items
        self.assertEqual(stats["ideal_fees"], Decimal("0.78"))

    def test_page_shows_only_own_data(self):
        self.client.force_login(self.admin_auth_user)  # admins can preview, but only their own
        response = self.client.get("/mapped")
        self.assertContains(response, "Admin User")
        self.assertContains(response, "Nothing yet")

    def test_page_closed_outside_window(self):
        with patch("admin_board_view.views.mapped_open", return_value=False):
            self.client.force_login(self.normal_auth_user)
            self.assertEqual(self.client.get("/mapped").status_code, 302)
