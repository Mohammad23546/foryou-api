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
        
        subject = 'تفعيل حسابك'
        message = f'''
        مرحباً {user.username}،
        
        لتفعيل حسابك يرجى النقر على الرابط التالي:
        {verification_url}
        
        إذا لم تقم بإنشاء هذا الحساب، يرجى تجاهل هذا البريد.
        '''
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False
        )
        
        print(f"Verification email sent to {user.email} with URL: {verification_url}")
        return token
        
    except Exception as e:
        print(f"Error sending verification email: {str(e)}")
        raise 