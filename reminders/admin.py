from django.contrib import admin
from .models import Reminder

@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'date', 'time', 'isCompleted')
    list_filter = ('type', 'isCompleted', 'date')
    search_fields = ('title', 'description')
    ordering = ('date', 'time')
