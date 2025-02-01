from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('change-password/', views.change_password, name='change_password'),
    path('verify-email/', views.verify_email, name='verify-email'),
    path('refresh-token/', views.refresh_token, name='refresh-token'),
] 