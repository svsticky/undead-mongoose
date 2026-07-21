from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from mongoose_app.models import User as MongooseUser, Product, Category, VAT

AuthUser = get_user_model()

class AdminBoardViewTests(TestCase):
    def setUp(self):
        # Create test category and vat for product creation if needed
        self.category = Category.objects.create(name="Test Category", order=1)
        self.vat = VAT.objects.create(percentage=21)

        # Create normal user in auth and mongoose
        self.normal_auth_user = AuthUser.objects.create_user(
            username="kc-uuid-normal",
            email="normal@example.com",
            password="password"
        )
        self.normal_mongoose_user = MongooseUser.objects.create(
            user_id="kc-uuid-normal",
            balance=15.00
        )

        # Create admin user in auth and mongoose
        self.admin_auth_user = AuthUser.objects.create_superuser(
            username="kc-uuid-admin",
            email="admin@example.com",
            password="password"
        )
        self.admin_mongoose_user = MongooseUser.objects.create(
            user_id="kc-uuid-admin",
            balance=50.00
        )

        self.client = Client()

    def test_index_normal_user_sees_user_home(self):
        self.client.force_login(self.normal_auth_user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user_home.html")

    def test_index_admin_user_sees_user_home(self):
        self.client.force_login(self.admin_auth_user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user_home.html")

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
