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
    email = claims.get('email') or (auth_user.email if auth_user else None)
    if not email:
        return None

    mongoose_user = MongooseUser.objects.filter(email=email).first()
    if mongoose_user:
        return mongoose_user

    # Determine student number / user_id
    student_num = claims.get('student_number')
    if isinstance(student_num, list) and len(student_num) > 0:
        student_num = student_num[0]

    user_id = None
    if student_num:
        try:
            user_id = int(student_num)
        except (ValueError, TypeError):
            pass

    if user_id is None:
        attrs = claims.get('attributes', {})
        if isinstance(attrs, dict) and 'student_number' in attrs:
            sn = attrs['student_number']
            if isinstance(sn, list) and len(sn) > 0:
                sn = sn[0]
            try:
                user_id = int(sn)
            except (ValueError, TypeError):
                pass

    if user_id is None or MongooseUser.objects.filter(user_id=user_id).exists():
        max_id = MongooseUser.objects.aggregate(models.Max('user_id'))['user_id__max'] or 1000000
        user_id = max_id + 1

    first_name = claims.get('given_name') or claims.get('firstName') or claims.get('first_name') or ''
    last_name = claims.get('family_name') or claims.get('lastName') or claims.get('last_name') or ''
    infix = claims.get('infix') or ''

    if claims.get('name'):
        name = claims['name']
    elif first_name or last_name:
        name = f"{first_name} {infix} {last_name}".strip() if infix else f"{first_name} {last_name}".strip()
    else:
        name = email.split('@')[0]

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
        user_id=user_id,
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

