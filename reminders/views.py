from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Reminder
from .serializers import ReminderSerializer
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from rest_framework.decorators import authentication_classes, permission_classes, api_view
from rest_framework_simplejwt.authentication import JWTAuthentication
from .utils import analyze_spoken_time
from rest_framework.exceptions import ValidationError

@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
class ReminderViewSet(viewsets.ModelViewSet):
    serializer_class = ReminderSerializer
    
    def get_queryset(self):
        return Reminder.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # تحقق من عدم وجود تذكير مماثل في نفس الوقت
        title = serializer.validated_data.get('title')
        date = serializer.validated_data.get('date')
        time = serializer.validated_data.get('time')
        period = serializer.validated_data.get('period')
        
        # تحقق من التذكيرات المتشابهة في آخر 24 ساعة
        one_day_ago = timezone.now() - timedelta(days=1)
        if Reminder.objects.filter(
            user=self.request.user,
            title=title,
            date=date,
            time=time,
            period=period,
            created_at__gte=one_day_ago
        ).exists():
            raise ValidationError({
                'error': 'لديك تذكير مماثل تم إنشاؤه مؤخراً'
            })
            
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def analyze_time(request):
    try:
        spoken_text = request.data.get('spokenText', '')
        if not spoken_text:
            return Response({
                'error': 'spokenText is required',
                'isValid': False
            }, status=status.HTTP_400_BAD_REQUEST)
            
        return analyze_spoken_time(spoken_text)
        
    except Exception as e:
        return Response({
            'error': str(e),
            'isValid': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
