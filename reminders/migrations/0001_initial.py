# Generated by Django 5.1.4 on 2025-01-17 06:19

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RecurringPattern',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('daily', 'يومي'), ('weekly', 'أسبوعي'), ('monthly', 'شهري')], max_length=10)),
                ('week_days', models.JSONField(blank=True, null=True)),
                ('month_days', models.JSONField(blank=True, null=True)),
                ('end_date', models.DateTimeField(blank=True, null=True)),
                ('occurrences', models.IntegerField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Reminder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, null=True)),
                ('icon', models.IntegerField()),
                ('color', models.IntegerField()),
                ('is_completed', models.BooleanField(default=False)),
                ('date', models.DateField()),
                ('time', models.TimeField()),
                ('type', models.CharField(choices=[('task', 'مهمة'), ('event', 'حدث'), ('birthday', 'عيد ميلاد'), ('other', 'آخر')], max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('recurring_pattern', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='reminders.recurringpattern')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reminders', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['date', 'time'],
            },
        ),
        migrations.CreateModel(
            name='SkippedOccurrence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('reminder', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='skipped_dates', to='reminders.reminder')),
            ],
            options={
                'unique_together': {('reminder', 'date')},
            },
        ),
    ]
