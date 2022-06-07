from mozilla_django_oidc.auth import OIDCAuthenticationBackend
#from myapp.models import Profile

class UndeadMongooseOIDC(OIDCAuthenticationBackend):
    def create_user(self, claims):
        user = super(UndeadMongooseOIDC, self).create_user(claims)
        if claims['is_admin']:
            user.is_superuser = True
            user.is_staff = True
        user.username = claims['email']
        user.save()

        return user

    def update_user(self, user, claims):
        if claims['is_admin']:
            user.is_superuser = True
            user.is_staff = True
        user.username = claims['email']
        user.save()

        return user