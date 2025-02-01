from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import uuid

def send_verification_email(user, token):
    try:
        token_str = str(token).replace('-', '')
        token_uuid = f"{token_str[:8]}-{token_str[8:12]}-{token_str[12:16]}-{token_str[16:20]}-{token_str[20:]}"
        verification_link = f"{settings.API_BASE_URL}/api/auth/verify-email/{token_uuid}/"
        
        context = {
            'user': user,
            'verification_link': verification_link
        }
        
        html_message = render_to_string('email/verification_email.html', context)
        plain_message = strip_tags(html_message)
        
        # إرسال البريد
        send_mail(
            subject='تأكيد البريد الإلكتروني',
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        print(f"خطأ في إرسال البريد: {str(e)}")
        return False 