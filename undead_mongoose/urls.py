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
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.urls import path, include, reverse
from django.conf import settings
from django.views import View

class CustomLogin(View):
    def get(self, request, **kwargs):
        print(request.GET)
        check = request.GET['next'].split("?") if 'next' in request.GET else []
        if len(check) == 2 and check[1] == 'logged':
            return HttpResponseRedirect('/denied/')
        else:
            return HttpResponseRedirect(
                reverse('oidc_authentication_init') + (
                    '?next={}?logged'.format(request.GET['next']) if 'next' in request.GET else ''
                )
            )

class DenyView(View):
    def get(self, request, **kwargs):
        return HttpResponseForbidden("You are not allowed to reach the admin side of Undead Mongoose")

urlpatterns = [
    path('admin/login/', CustomLogin.as_view()),
    path('admin/', admin.site.urls),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('denied/', DenyView.as_view()),
    path('api/', include('mongoose_app.urls')),
    path('', include('admin_board_view.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
