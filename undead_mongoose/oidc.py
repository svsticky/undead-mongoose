from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from mongoose_app.models import User as MongooseUser
from decimal import Decimal

def is_admin_user(claims):
    return claims.get('is_admin')

def ensure_mongoose_user(claims, auth_user=None):
    user_id = claims.get('sub')
    if not user_id:
        return None

    mongoose_user = MongooseUser.objects.filter(user_id=user_id).first()
    if mongoose_user:
        return mongoose_user

    return MongooseUser.objects.create(
        user_id=user_id,
        balance=Decimal("0.00"),
    )

class UndeadMongooseOIDC(OIDCAuthenticationBackend):
    def create_user(self, claims):
        user = super(UndeadMongooseOIDC, self).create_user(claims)
        if is_admin_user(claims):
            user.is_superuser = True
            user.is_staff = True
        user.username = claims.get('sub', user.username)
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
        user.save()

        ensure_mongoose_user(claims, user)
        return user
