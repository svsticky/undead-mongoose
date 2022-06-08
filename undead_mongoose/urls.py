"""undead_mongoose URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls.static import static
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import path, include, reverse
from django.conf import settings
from django.views import View

class CustomLogin(View):
    def get(self, request, **kwargs):
        print(request)
        if 'logged' not in request.GET:
            return HttpResponseRedirect(
                reverse('oidc_authentication_init') + (
                    '?next=/admin/?logged=true'#.format(request.GET['next']) if 'next' in request.GET else ''
                )
            )
        else:
            return HttpResponse("Access denied!")

urlpatterns = [
    path('admin/login/', CustomLogin.as_view()),
    path('admin/', admin.site.urls),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('', include('mongoose_app.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
