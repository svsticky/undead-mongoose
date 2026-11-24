import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.http import HttpResponse
from django.core.cache import cache
from mongoose_app.models import User, Card
from mongoose_app.views import register_card
from mongoose_app.keycloak import get_keycloak_user_by_student_number

@override_settings(
    KEYCLOAK_URL="http://keycloak.local:8080",
    KEYCLOAK_REALM="test-realm",
    KEYCLOAK_CLIENT_ID="test-client",
    KEYCLOAK_CLIENT_SECRET="test-secret",
    USER_TOKEN="dummy_token",
    API_TOKEN="test-api-token"
)
class KeycloakIntegrationTests(TestCase):
    def setUp(self):
        User.objects.all().delete()
        Card.objects.all().delete()
        cache.clear()

    @patch("mongoose_app.keycloak.requests.post")
    @patch("mongoose_app.keycloak.requests.get")
    def test_get_keycloak_user_by_student_number_success(self, mock_get, mock_post):
        # Mock token response
        mock_post_resp = MagicMock()
        mock_post_resp.json.return_value = {"access_token": "mock-token"}
        mock_post.return_value = mock_post_resp

        # Mock user search response
        mock_get_resp = MagicMock()
        mock_get_resp.json.return_value = [
            {
                "id": "uuid-123",
                "username": "student1",
                "firstName": "John",
                "lastName": "Doe",
                "email": "john.doe@example.com",
                "attributes": {
                    "student_number": ["123456"],
                    "birthday": ["1999-12-31"]
                }
            }
        ]
        mock_get.return_value = mock_get_resp

        user = get_keycloak_user_by_student_number("123456")
        self.assertIsNotNone(user)
        self.assertEqual(user["email"], "john.doe@example.com")
        self.assertEqual(user["firstName"], "John")

        # Verify POST token request params
        mock_post.assert_called_once_with(
            "http://keycloak.local:8080/realms/test-realm/protocol/openid-connect/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "test-client",
                "client_secret": "test-secret"
            }
        )

        # Verify GET user request params
        mock_get.assert_called_once_with(
            "http://keycloak.local:8080/admin/realms/test-realm/users",
            headers={
                "Authorization": "Bearer mock-token",
                "Accept": "application/json"
            },
            params={"q": "student_number:123456"}
        )

    @patch("mongoose_app.keycloak.requests.post")
    @patch("mongoose_app.keycloak.requests.get")
    def test_get_keycloak_user_by_student_number_not_found(self, mock_get, mock_post):
        mock_post_resp = MagicMock()
        mock_post_resp.json.return_value = {"access_token": "mock-token"}
        mock_post.return_value = mock_post_resp

        mock_get_resp = MagicMock()
        mock_get_resp.json.return_value = []
        mock_get.return_value = mock_get_resp

        user = get_keycloak_user_by_student_number("999999")
        self.assertIsNone(user)

    @patch("mongoose_app.models.get_cached_keycloak_user")
    @patch("mongoose_app.views.get_keycloak_user_by_student_number")
    @patch("mongoose_app.views.send_confirmation")
    def test_register_card_user_creation(self, mock_send_conf, mock_get_kc_user, mock_cached_profile):
        keycloak_profile = {
            "id": "uuid-123",
            "username": "student123",
            "firstName": "Jane",
            "lastName": "Doe",
            "email": "jane.doe@example.com",
            "attributes": {
                "student_number": ["1234567"],
                "birthday": ["2001-05-15"],
                "infix": ["van"]
            }
        }
        mock_get_kc_user.return_value = keycloak_profile
        mock_cached_profile.return_value = keycloak_profile

        # Mock requests client representation
        request_mock = MagicMock()
        request_mock.body = b'{"student": "1234567", "uuid": "carduuid"}'
        request_mock.headers = {"Authorization": "test-api-token"}
        request_mock.method = "POST"

        # Call register_card
        with patch("mongoose_app.views.authenticated", lambda x: x):
            response = register_card(request_mock)

        self.assertEqual(response.status_code, 201)

        # Check if user is created in database
        user = User.objects.get(user_id="uuid-123")
        self.assertEqual(user.name, "Jane van Doe")
        self.assertEqual(user.email, "jane.doe@example.com")
        self.assertEqual(str(user.birthday), "2001-05-15")

        # Check if card is created
        card = Card.objects.get(card_id="carduuid")
        self.assertEqual(card.user_id, user)
        self.assertFalse(card.active)

        mock_send_conf.assert_called_once_with("jane.doe@example.com", card)

    def test_is_admin_user_variants(self):
        from undead_mongoose.oidc import is_admin_user

        # Case 1: Direct claim
        self.assertTrue(is_admin_user({"is_admin": True}))
        self.assertFalse(is_admin_user({"is_admin": False}))

        # Case 2: Realm roles
        self.assertTrue(is_admin_user({"realm_access": {"roles": ["user", "admin"]}}))
        self.assertFalse(is_admin_user({"realm_access": {"roles": ["user"]}}))

        # Case 3: Client roles
        self.assertTrue(is_admin_user({"resource_access": {"mongoose-client": {"roles": ["admin"]}}}))
        self.assertFalse(is_admin_user({"resource_access": {"mongoose-client": {"roles": ["user"]}}}))
        self.assertFalse(is_admin_user({}))



@override_settings(API_TOKEN="test-api-token")
class ProductByBarcodeTests(TestCase):
    def setUp(self):
        from mongoose_app.models import Category, Configuration, Product, VAT

        Configuration.objects.update_or_create(pk=1, defaults={"alc_time": "00:00:00"})
        vat = VAT.objects.create(percentage=9)
        food = Category.objects.create(name="Food")
        drinks = Category.objects.create(name="Beer", alcoholic=True)
        self.user = User.objects.create(user_id="kc-user")
        Card.objects.create(card_id="CARD0001", active=True, user_id=self.user)
        Product.objects.create(name="Wafel", price="0.50", vat=vat, category=food, barcode="111")
        Product.objects.create(name="Old", price="1.00", vat=vat, category=food, barcode="222", enabled=False)
        Product.objects.create(name="Pils", price="1.00", vat=vat, category=drinks, barcode="333")

    def get(self, barcode, uuid="CARD0001"):
        return self.client.get(
            "/api/product/barcode",
            {"uuid": uuid, "barcode": barcode},
            HTTP_AUTHORIZATION="test-api-token",
        )

    def birthday(self, value):
        from unittest.mock import PropertyMock
        return patch.object(User, "birthday", new_callable=PropertyMock, return_value=value)

    # Enabled, non-alcoholic product is returned with its barcode.
    def test_found(self):
        response = self.get("111")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Wafel")
        self.assertEqual(response.json()["barcode"], "111")

    # A barcode no product has gives 404.
    def test_unknown_barcode(self):
        self.assertEqual(self.get("999").status_code, 404)

    # An unknown card gives 404, even for a valid barcode.
    def test_unknown_card(self):
        self.assertEqual(self.get("111", uuid="NOPE").status_code, 404)

    # An inactive card gives 404, even for a valid barcode.
    def test_inactive_card(self):
        Card.objects.create(card_id="CARD0002", active=False, user_id=self.user)
        self.assertEqual(self.get("111", uuid="CARD0002").status_code, 404)

    # A request without a barcode gives 400 instead of matching products without one.
    def test_missing_barcode(self):
        response = self.client.get(
            "/api/product/barcode", {"uuid": "CARD0001"}, HTTP_AUTHORIZATION="test-api-token"
        )
        self.assertEqual(response.status_code, 400)

    # A whitespace-only barcode gives 400.
    def test_blank_barcode(self):
        self.assertEqual(self.get("  ").status_code, 400)

    # Surrounding whitespace (e.g. a scanner's CR/LF) is stripped before matching.
    def test_barcode_whitespace_stripped(self):
        response = self.get(" 111\r\n")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Wafel")

    # A disabled product gives 410 (no longer for sale).
    def test_disabled_product(self):
        self.assertEqual(self.get("222").status_code, 410)

    # A 16-year-old may not buy an alcoholic product (403).
    def test_alcohol_underage(self):
        from datetime import date
        with self.birthday(date(date.today().year - 16, 1, 1)):
            self.assertEqual(self.get("333").status_code, 403)

    # Without a known birthday the user is treated as underage (403).
    def test_alcohol_unknown_birthday(self):
        with self.birthday(None):
            self.assertEqual(self.get("333").status_code, 403)

    # An adult may buy an alcoholic product after the alcohol time (200).
    def test_alcohol_adult(self):
        from datetime import date
        with self.birthday(date(1990, 1, 1)):
            self.assertEqual(self.get("333").status_code, 200)

    # Requests without the API token are rejected (403).
    def test_requires_token(self):
        response = self.client.get("/api/product/barcode", {"uuid": "CARD0001", "barcode": "111"})
        self.assertEqual(response.status_code, 403)
