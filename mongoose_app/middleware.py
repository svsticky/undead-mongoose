from functools import wraps
from django.conf import settings
from django.http.response import HttpResponse

# This decorator function checks for an authorization header before the view function is called.
# ONLY USE WITH A VIEW FUNCTION, EXPECTS A REQUEST OBJECT TO BE IN ARGS!
def authenticated(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        request = args[0]
        if not "Authorization" in request.headers.keys():
            return HttpResponse(status=403)
        
        auth_token = request.headers["Authorization"]
        if auth_token == settings.API_TOKEN:
            return f(request)
        
        return HttpResponse(status=403)
    return decorator