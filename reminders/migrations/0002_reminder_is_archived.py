# Generated by Django 5.1.4 on 2025-01-17 06:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reminders', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='reminder',
            name='is_archived',
            field=models.BooleanField(default=False),
        ),
    ]
