"""
URL configuration for foryouproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from accounts.views import clear_database

def home(request):
    return JsonResponse({
        "status": "success",
        "message": "API is running",
        "endpoints": {
            "auth": "https://foryou-api.onrender.com/api/auth/",
            "reminders": "https://foryou-api.onrender.com/api/"
        }
    })

urlpatterns = [
    path('', home),  # صفحة رئيسية تعرض حالة API
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/', include('reminders.urls')),
    path('api/clear-database/', clear_database, name='clear_database'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
