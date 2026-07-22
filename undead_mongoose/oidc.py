from mozilla_django_oidc.auth import OIDCAuthenticationBackend

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

class UndeadMongooseOIDC(OIDCAuthenticationBackend):
    def create_user(self, claims):
        user = super(UndeadMongooseOIDC, self).create_user(claims)
        if is_admin_user(claims):
            user.is_superuser = True
            user.is_staff = True
        user.username = claims.get('email', user.username)
        user.save()

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

        return user

