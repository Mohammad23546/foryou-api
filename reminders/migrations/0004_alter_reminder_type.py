# Generated by Django 5.1.4 on 2025-01-18 06:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reminders', '0003_remove_reminder_recurring_pattern_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reminder',
            name='type',
            field=models.CharField(choices=[('الأصدقاء', 'الأصدقاء'), ('العائلة', 'العائلة'), ('العمل', 'العمل'), ('الدراسة', 'الدراسة'), ('طعام صحي', 'طعام صحي'), ('رياضة', 'رياضة'), ('تسوق', 'تسوق'), ('العادات اليومية', 'العادات اليومية'), ('أخرى', 'أخرى')], max_length=20),
        ),
    ]
