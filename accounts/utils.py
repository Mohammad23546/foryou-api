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
    payload = {
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(days=1),  # التوكن صالح لمدة يوم واحد
        'iat': datetime.utcnow(),
        'type': 'email_verification'
    }
    
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token

def send_verification_email(user, token):
    try:
        verification_url = f"https://foryou-api.onrender.com/api/auth/verify-email/?token={token}"
        
        # قراءة قالب البريد
        html_message = render_to_string('email/verification_email.html', {
            'user': user,
            'verification_url': verification_url
        })
        
        # إرسال البريد
        send_mail(
            subject='تفعيل حسابك',
            message=strip_tags(html_message),
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        print(f"Verification email sent to {user.email} with URL: {verification_url}")
        return True
        
    except Exception as e:
        print(f"Error sending verification email: {str(e)}")
        return False 