import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.http import HttpResponse
from mongoose_app.models import User, Card
from mongoose_app.views import get_keycloak_user_by_student_number, register_card

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

    @patch("mongoose_app.views.requests.post")
    @patch("mongoose_app.views.requests.get")
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
                    "birth_date": ["1999-12-31"]
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

    @patch("mongoose_app.views.requests.post")
    @patch("mongoose_app.views.requests.get")
    def test_get_keycloak_user_by_student_number_not_found(self, mock_get, mock_post):
        mock_post_resp = MagicMock()
        mock_post_resp.json.return_value = {"access_token": "mock-token"}
        mock_post.return_value = mock_post_resp

        mock_get_resp = MagicMock()
        mock_get_resp.json.return_value = []
        mock_get.return_value = mock_get_resp

        user = get_keycloak_user_by_student_number("999999")
        self.assertIsNone(user)

    @patch("mongoose_app.views.get_keycloak_user_by_student_number")
    @patch("mongoose_app.views.send_confirmation")
    def test_register_card_user_creation(self, mock_send_conf, mock_get_kc_user):
        mock_get_kc_user.return_value = {
            "id": "uuid-123",
            "username": "student123",
            "firstName": "Jane",
            "lastName": "Doe",
            "email": "jane.doe@example.com",
            "attributes": {
                "student_number": ["1234567"],
                "birth_date": ["2001-05-15"],
                "infix": ["van"]
            }
        }

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
        user = User.objects.get(user_id=1234567)
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

