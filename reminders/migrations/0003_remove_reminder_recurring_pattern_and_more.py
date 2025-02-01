# Generated by Django 5.1.4 on 2025-01-18 05:32

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reminders', '0002_reminder_is_archived'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reminder',
            name='recurring_pattern',
        ),
        migrations.AlterUniqueTogether(
            name='skippedoccurrence',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='skippedoccurrence',
            name='reminder',
        ),
        migrations.AlterModelOptions(
            name='reminder',
            options={},
        ),
        migrations.RemoveField(
            model_name='reminder',
            name='is_archived',
        ),
        migrations.RemoveField(
            model_name='reminder',
            name='is_completed',
        ),
        migrations.AddField(
            model_name='reminder',
            name='isCompleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='reminder',
            name='recurringPattern',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='reminder',
            name='description',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='reminder',
            name='time',
            field=models.CharField(max_length=5),
        ),
        migrations.AlterField(
            model_name='reminder',
            name='type',
            field=models.CharField(choices=[('الأصدقاء', 'الأصدقاء'), ('العائلة', 'العائلة'), ('العمل', 'العمل'), ('الدراسة', 'الدراسة'), ('طعام صحي', 'طعام صحي'), ('رياضة', 'رياضة'), ('تسوق', 'تسوق'), ('أخرى', 'أخرى')], max_length=20),
        ),
        migrations.AlterField(
            model_name='reminder',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.DeleteModel(
            name='RecurringPattern',
        ),
        migrations.DeleteModel(
            name='SkippedOccurrence',
        ),
    ]
