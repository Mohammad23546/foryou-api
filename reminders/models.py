from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

class Reminder(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    isCompleted = models.BooleanField(default=False)
    date = models.DateField()
    time = models.CharField(max_length=5)
    period = models.CharField(max_length=10, default='صباحاً')
    type = models.CharField(max_length=50)
    recurringPattern = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
