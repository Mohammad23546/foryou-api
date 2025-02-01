from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReminderViewSet
from . import views

router = DefaultRouter()
router.register('reminders', ReminderViewSet, basename='reminder')

urlpatterns = [
    path('', include(router.urls)),
    path('analyze-time/', views.analyze_time, name='analyze_time'),
] 