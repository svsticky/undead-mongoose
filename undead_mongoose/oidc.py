from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from mongoose_app.models import User as MongooseUser
from django.db import models
from decimal import Decimal
from datetime import datetime, date

def is_admin_user(claims):
    return claims.get('is_admin')

def ensure_mongoose_user(claims, auth_user=None):
    email = claims.get('email') or (auth_user.email if auth_user else None)
    if not email:
        return None

    user_id = claims.get('sub')
    if not user_id:
        return None

    mongoose_user = MongooseUser.objects.filter(user_id=user_id).first()

    if mongoose_user:
        return mongoose_user

    sub = claims.get('sub')
    if not sub:
        return None

    name = claims['name']

    birth_date_str = claims.get('birthday') or claims.get('attributes', {}).get('birthday') or claims.get('birth_date')
    if isinstance(birth_date_str, list) and len(birth_date_str) > 0:
        birth_date_str = birth_date_str[0]
    born = date(2000, 1, 1)
    if birth_date_str:
        try:
            born = datetime.strptime(str(birth_date_str), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            pass

    return MongooseUser.objects.create(
        user_id=sub,
        name=name,
        birthday=born,
        email=email,
        balance=Decimal("0.00"),
    )

class UndeadMongooseOIDC(OIDCAuthenticationBackend):
    def create_user(self, claims):
        user = super(UndeadMongooseOIDC, self).create_user(claims)
        if is_admin_user(claims):
            user.is_superuser = True
            user.is_staff = True
        user.username = claims.get('email', user.username)
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
        user.username = claims.get('email', user.username)
        user.save()

        ensure_mongoose_user(claims, user)
        return user

