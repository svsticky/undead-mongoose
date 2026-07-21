from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from mongoose_app.models import User as MongooseUser
from django.db import models
from decimal import Decimal
from datetime import datetime, date

def is_admin_user(claims):
    # Check for direct is_admin claim
    if claims.get('is_admin'):
        return True
    # Check for realm level admin role
    realm_access = claims.get('realm_access', {})
    if 'admin' in realm_access.get('roles', []):
        return True
    # Check for client level admin role
    resource_access = claims.get('resource_access', {})
    for client in resource_access.values():
        if 'admin' in client.get('roles', []):
            return True
    return False

def ensure_mongoose_user(claims, auth_user=None):
    keycloak_id = claims.get('sub') or (auth_user.username if auth_user else None)
    if not keycloak_id:
        return None

    mongoose_user = MongooseUser.objects.filter(user_id=keycloak_id).first()
    if mongoose_user:
        return mongoose_user

    return MongooseUser.objects.create(
        user_id=keycloak_id,
        balance=Decimal("0.00"),
    )

class UndeadMongooseOIDC(OIDCAuthenticationBackend):
    def get_user_id(self, claims):
        return claims.get('sub')

    def create_user(self, claims):
        user = super(UndeadMongooseOIDC, self).create_user(claims)
        if is_admin_user(claims):
            user.is_superuser = True
            user.is_staff = True
        user.username = claims.get('sub', user.username)
        user.email = claims.get('email', user.email)
        user.save()

        ensure_mongoose_user(claims, user)
        return user

    def update_user(self, user, claims):
        if is_admin_user(claims):
            user.is_superuser = True
            user.is_staff = True
        else:
            user.is_superuser = False
            user.is_staff = False
        user.username = claims.get('sub', user.username)
        user.email = claims.get('email', user.email)
        user.save()

        ensure_mongoose_user(claims, user)
        return user

