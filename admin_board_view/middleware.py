from functools import wraps
from django.http.response import HttpResponseRedirect

# Decorator to check if a user is authenticated
def dashboard_authenticated(f):
    """
    Check if the user is logged in, if not redirect to login page
    """
    @wraps(f)
    def decorator(*args, **kwargs):
        request = args[0]
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login")
        
        return f(*args, **kwargs)
    return decorator


def dashboard_admin(f):
    """
    Check if the user is logged in and is an admin, if not redirect to login page
    """
    @wraps(f)
    def decorator(*args, **kwargs):
        request = args[0]
        if not request.user.is_superuser:
            return HttpResponseRedirect("/login")

        return f(*args, **kwargs)
    return decorator
