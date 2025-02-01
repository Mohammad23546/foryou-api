from rest_framework import serializers
from .models import Reminder
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from django.db import transaction
import hashlib

class ReminderSerializer(serializers.ModelSerializer):
    # تعريف id كحقل نصي
    id = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Reminder
        fields = [
            'id', 'title', 'description',
            'isCompleted', 'date', 'time', 'period',
            'type', 'recurringPattern', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def _generate_lock_key(self, data, user):
        """توليد مفتاح فريد للقفل"""
        key_data = f"{user.id}:{data['title']}:{data['date']}:{data['time']}"
        return f"reminder_lock:{hashlib.md5(key_data.encode()).hexdigest()}"

    def create(self, validated_data):
        user = self.context['request'].user
        
        with transaction.atomic():
            # التحقق من عدم وجود تذكير مماثل
            time_threshold = timezone.now() - timedelta(seconds=30)
            existing_reminder = Reminder.objects.select_for_update().filter(
                user=user,
                title=validated_data['title'],
                date=validated_data['date'],
                time=validated_data['time'],
                created_at__gte=time_threshold
            ).exists()

            if existing_reminder:
                raise serializers.ValidationError(
                    "تم إنشاء تذكير مماثل مؤخراً. الرجاء الانتظار قليلاً قبل المحاولة مرة أخرى."
                )

            validated_data['user'] = user
            reminder = super().create(validated_data)
            return reminder

    def validate(self, data):
        # التحقق من عدم وجود تذكير مماثل في نفس الوقت
        user = self.context['request'].user
        time_threshold = timezone.now() - timedelta(seconds=30)  # منع التكرار خلال 30 ثانية

        existing_reminder = Reminder.objects.filter(
            user=user,
            title=data['title'],
            date=data['date'],
            time=data['time'],
            period=data['period'],
            created_at__gte=time_threshold
        ).exists()

        if existing_reminder:
            raise serializers.ValidationError("تم إنشاء تذكير مماثل مؤخراً. الرجاء الانتظار قليلاً قبل المحاولة مرة أخرى.")

        # معالجة النصوص العربية
        for field in ['title', 'description', 'type', 'period']:
            if field in data and data[field]:
                try:
                    text = data[field]
                    if isinstance(text, bytes):
                        text = text.decode('utf-8')
                    elif isinstance(text, str):
                        text = text.encode('utf-8').decode('utf-8')
                    data[field] = text
                except UnicodeError:
                    raise serializers.ValidationError(f"خطأ في ترميز النص في حقل {field}")
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        # تحويل ID إلى نص
        if data.get('id'):
            data['id'] = str(data['id'])
            
        # معالجة النصوص العربية
        for field in ['title', 'description', 'type', 'period']:
            if data.get(field):
                try:
                    text = data[field]
                    if isinstance(text, bytes):
                        text = text.decode('utf-8')
                    elif isinstance(text, str):
                        text = text.encode('raw_unicode_escape').decode('unicode_escape')
                    data[field] = text
                except Exception as e:
                    print(f"خطأ في معالجة الحقل {field}: {str(e)}")
                    
        data['isCompleted'] = bool(data['isCompleted'])
        return data 