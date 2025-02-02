from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import uuid
import jwt
from datetime import datetime, timedelta

def generate_verification_token(user):
    """
    إنشاء توكن للتحقق من البريد الإلكتروني
    """
    token = jwt.encode({
        'user_id': user.id,
        'type': 'email_verification',
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)  # صالح لمدة يوم
    }, settings.SECRET_KEY, algorithm='HS256')
    return token

def send_verification_email(user):
    token = generate_verification_token(user)
    verification_url = f"{settings.SITE_URL}/api/auth/verify-email/?token={token}"
    
    html_message = render_to_string('email/verification_email.html', {
        'user': user,
        'verification_url': verification_url
    })
    
    send_mail(
        subject='تفعيل حسابك',
        message=f'مرحباً {user.username}،\nلتفعيل حسابك يرجى النقر على الرابط التالي:\n{verification_url}',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
        html_message=html_message
    )
    return token 