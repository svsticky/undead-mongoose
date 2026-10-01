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


class WrappedTests(TestCase):
    def setUp(self):
        AdminBoardViewTests.setUp(self)
        from datetime import date
        from mongoose_app.models import Configuration, SaleTransaction, ProductTransactions
        from admin_board_view import views
        self.views, self.date = views, date
        Configuration.objects.create()
        cola = Product.objects.create(name="Cola", price=1, category=self.category, vat=self.vat)
        mars = Product.objects.create(name="Mars", price=1, category=self.category, vat=self.vat)
        for product, amount, cancelled in [(cola, 3, False), (mars, 1, False), (mars, 9, True)]:
            sale = SaleTransaction.objects.create(user_id=self.normal_mongoose_user, transaction_sum=amount, cancelled=cancelled)
            ProductTransactions.objects.create(product_id=product, transaction_id=sale, product_price=1, product_vat=21, amount=amount)

    def test_window_defaults_to_june(self):
        d = self.date
        self.assertTrue(self.views.wrapped_open(d(2027, 6, 15)))
        self.assertFalse(self.views.wrapped_open(d(2027, 7, 1)))

    def test_stats_ignore_cancelled_sales(self):
        stats = self.views.wrapped_stats(self.normal_mongoose_user)
        self.assertEqual(stats["visits"], 2)
        self.assertEqual(stats["items"], 4)
        self.assertEqual(stats["top_products"][0]["product_id__name"], "Cola")
        self.assertEqual(stats["alcohol_pct"], 0)
        self.assertEqual(stats["ideal_fees"], 0)

    def test_alcohol_and_ideal_fee_stats(self):
        from mongoose_app.models import Category, IDealTransaction, PaymentStatus, SaleTransaction, ProductTransactions
        beer = Product.objects.create(name="Beer", price=1, vat=self.vat,
                                      category=Category.objects.create(name="Bier", alcoholic=True))
        sale = SaleTransaction.objects.create(user_id=self.normal_mongoose_user, transaction_sum=4)
        ProductTransactions.objects.create(product_id=beer, transaction_id=sale, product_price=1, product_vat=21, amount=4)
        for status in [PaymentStatus.PAID, PaymentStatus.PAID, PaymentStatus.CANCELLED]:
            IDealTransaction.objects.create(user_id=self.normal_mongoose_user, transaction_sum=10, status=status)
        stats = self.views.wrapped_stats(self.normal_mongoose_user)
        self.assertEqual(stats["alcohol_pct"], 50)  # 4 beers out of 8 items
        self.assertEqual(stats["ideal_fees"], Decimal("0.78"))

    def test_page_shows_only_own_data(self):
        self.client.force_login(self.admin_auth_user)  # admins can preview, but only their own
        response = self.client.get("/wrapped")
        self.assertContains(response, "Admin User")
        self.assertContains(response, "Nothing yet")

    def test_page_closed_outside_window(self):
        with patch("admin_board_view.views.wrapped_open", return_value=False):
            self.client.force_login(self.normal_auth_user)
            self.assertEqual(self.client.get("/wrapped").status_code, 302)
