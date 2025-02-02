from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import uuid
import jwt
import datetime

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
    try:
        token = generate_verification_token(user)
        verification_url = f"{settings.SITE_URL}/api/auth/verify-email/?token={token}"
        
        # استخدام القالب HTML
        html_message = render_to_string('email/verification_email.html', {
            'user': user,
            'verification_url': verification_url
        })
        
        # إرسال البريد بتنسيق HTML
        send_mail(
            subject='تفعيل حسابك في تطبيق لأجلك',
            message='',  # الرسالة النصية فارغة لأننا نستخدم HTML
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
        
        print(f"Verification email sent to {user.email} with URL: {verification_url}")
        return token
        
    except Exception as e:
        print(f"Error sending verification email: {str(e)}")
        raise 