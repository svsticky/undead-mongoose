"""
Helpers for talking to Keycloak's admin REST API using the mongoose-backend
service account (client credentials grant).

mongoose stores as little personal data as possible locally -- name, email
and birthday are not persisted, they are fetched from here on demand and
cached briefly (see get_cached_keycloak_user).
"""
import logging

from django.conf import settings
from django.core.cache import cache
import requests

logger = logging.getLogger(__name__)

KEYCLOAK_USER_CACHE_SECONDS = 300


def _get_admin_token():
    keycloak_url = settings.KEYCLOAK_URL
    realm = settings.KEYCLOAK_REALM
    client_id = settings.KEYCLOAK_CLIENT_ID
    client_secret = settings.KEYCLOAK_CLIENT_SECRET

    if not all([keycloak_url, realm, client_id, client_secret]):
        raise ValueError("Keycloak configuration is incomplete in settings.")

    token_url = f"{keycloak_url.rstrip('/')}/realms/{realm}/protocol/openid-connect/token"
    token_response = requests.post(token_url, data={
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    })
    token_response.raise_for_status()
    return token_response.json()["access_token"]


def get_keycloak_user_by_id(user_id):
    """
    Fetches a single user's representation from Keycloak by id (the same
    value as the OIDC `sub` claim). Returns None if Keycloak has no such
    user (e.g. they were deleted), or if user_id isn't a Keycloak id at
    all (e.g. a not-yet-migrated legacy account).
    """
    keycloak_url = settings.KEYCLOAK_URL
    realm = settings.KEYCLOAK_REALM
    token = _get_admin_token()

    user_url = f"{keycloak_url.rstrip('/')}/admin/realms/{realm}/users/{user_id}"
    response = requests.get(
        user_url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def get_cached_keycloak_user(user_id):
    """
    Same as get_keycloak_user_by_id, but cached for a short time so pages
    that render many users (admin dashboard, exports) don't fire one
    request per user per render.

    Used for passive display (User.name/email/birthday) -- so on any
    failure (bad config, Keycloak unreachable, etc.) this logs the error
    and returns None rather than raising, so a Keycloak outage degrades a
    name to "(unavailable)" instead of crashing the whole page. Failures
    aren't cached, so the next request retries rather than being stuck
    showing "(unavailable)" for the full TTL after a transient blip.
    """
    cache_key = f"keycloak-user:{user_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached or None

    try:
        user = get_keycloak_user_by_id(user_id)
    except Exception:
        logger.exception("Failed to fetch Keycloak user %s", user_id)
        return None

    # Cache a sentinel for "not found" too, so a deleted/legacy id doesn't
    # get looked up again on every single access within the TTL.
    cache.set(cache_key, user or False, KEYCLOAK_USER_CACHE_SECONDS)
    return user


def list_keycloak_users(max_results=100):
    """
    Lists users in the realm (used by the seed command to attach fake
    balances/cards to real Keycloak accounts instead of inventing ids that
    don't exist anywhere). Raises on failure -- unlike get_cached_keycloak_user,
    there's no reasonable silent fallback for "I need real users to seed with".
    """
    keycloak_url = settings.KEYCLOAK_URL
    realm = settings.KEYCLOAK_REALM
    token = _get_admin_token()

    users_url = f"{keycloak_url.rstrip('/')}/admin/realms/{realm}/users"
    response = requests.get(
        users_url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        params={"max": max_results},
    )
    response.raise_for_status()
    return response.json()


def get_keycloak_user_by_student_number(student_number):
    """
    Retrieves user information from Keycloak using Client Credentials.
    """
    keycloak_url = settings.KEYCLOAK_URL
    realm = settings.KEYCLOAK_REALM
    token = _get_admin_token()

    users_url = f"{keycloak_url.rstrip('/')}/admin/realms/{realm}/users"
    users_response = requests.get(
        users_url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        params={"q": f"student_number:{student_number}"},
    )
    users_response.raise_for_status()
    users_list = users_response.json()

    if not users_list:
        return None

    for u in users_list:
        attributes = u.get("attributes", {})
        std_num_list = attributes.get("student_number", [])
        if std_num_list and str(std_num_list[0]) == str(student_number):
            return u

    return users_list[0]
