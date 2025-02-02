from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
import logging
from django.http import JsonResponse, HttpResponse
import json
from .models import EmailVerification
from .utils import send_verification_email, generate_verification_token
from django.utils import timezone
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import AccessToken
from datetime import datetime, timedelta
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import BasePermission
from django.views.decorators.csrf import csrf_exempt
import uuid
from django.conf import settings
import jwt
from django.urls import reverse
from django.http import HttpResponseRedirect
from .serializers import UserSerializer

logger = logging.getLogger(__name__)

User = get_user_model()

class IsTokenValid(BasePermission):
    """التحقق من صلاحية لتوكن وعدم وجوده في القائمة السوداء"""
    
    def has_permission(self, request, view):
        try:
            auth = JWTAuthentication()
            validated_token = auth.get_validated_token(request.auth)
            
            # التحقق من وجود التوكن في القائمة السوداء
            is_blacklisted = BlacklistedToken.objects.filter(
                token__jti=validated_token['jti']
            ).exists()
            
            return not is_blacklisted
            
        except Exception as e:
            print(f"Token validation error: {str(e)}")
            return False

@api_view(['GET'])
def test(request):
    return Response({"message": "Hello, World!"}, status=status.HTTP_200_OK)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    try:
        email = request.data.get('email')
        username = request.data.get('username')
        password = request.data.get('password')

        if User.objects.filter(email=email).exists():
            return Response({
                'success': False,
                'message': 'البريد الإلكتروني مسجل مسبقاً',
                'code': 'EMAIL_EXISTS'
            }, status=400)

        user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            is_active=False
        )

        # إرسال بريد التفعيل
        try:
            send_verification_email(user)
        except Exception as e:
            print(f"Email sending error: {str(e)}")
            user.delete()  # حذف المستخدم إذا فشل إرسال البريد
            return Response({
                'success': False,
                'message': 'حدث خطأ أثناء إرسال بريد التفعيل',
                'code': 'EMAIL_SEND_ERROR'
            }, status=400)

        return Response({
            'success': True,
            'message': 'تم إنشاء الحساب بنجاح. يرجى التحقق من بريدك الإلكتروني',
            'code': 'REGISTRATION_SUCCESS'
        }, status=201)

    except Exception as e:
        print(f"Registration error: {str(e)}")
        return Response({
            'success': False,
            'message': 'حدث خطأ أثناء إنشاء الحساب',
            'code': 'REGISTRATION_ERROR'
        }, status=400)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    try:
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, email=email, password=password)

        if not user:
            return Response({
                'success': False,
                'message': 'البريد الإلكتروني أو كلمة المرور غير صحيحة',
                'code': 'INVALID_CREDENTIALS'
            }, status=401)

        if not user.is_active:
            return Response({
                'success': False,
                'message': 'الرجاء تفعيل حسابك من خلال البريد الإلكتروني',
                'code': 'ACCOUNT_NOT_ACTIVATED'
            }, status=401)

        refresh = RefreshToken.for_user(user)

        return Response({
            'success': True,
            'message': 'تم تسجيل الدخول بنجاح',
            'code': 'LOGIN_SUCCESS',
            'data': {
                'token': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username
                }
            }
        })

    except Exception as e:
        print(f"Login error: {str(e)}")
        return Response({
            'success': False,
            'message': 'حدث خطأ أثناء تسجيل الدخول. الرجاء المحاولة مرة أخرى',
            'code': 'LOGIN_ERROR'
        }, status=400)

@api_view(['GET'])
@renderer_classes([TemplateHTMLRenderer, JSONRenderer])
def verify_email(request):
    try:
        token = request.GET.get('token')
        if not token:
            return Response({
                'success': False,
                'message': 'رمز التحقق مفقود',
                'code': 'MISSING_TOKEN'
            }, status=400)

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user = User.objects.get(id=payload['user_id'])
            
            if user.is_active:
                return render(request, 'email/verification_success.html', {
                    'message': 'الحساب مفعل مسبقاً'
                })

            user.is_active = True
            user.save()

            return render(request, 'email/verification_success.html', {
                'message': 'تم تفعيل حسابك بنجاح! يمكنك الآن تسجيل الدخول'
            })

        except jwt.ExpiredSignatureError:
            return render(request, 'error.html', {
                'message': 'رابط التفعيل منتهي الصلاحية'
            })
        except (jwt.InvalidTokenError, User.DoesNotExist):
            return render(request, 'error.html', {
                'message': 'رابط التفعيل غير صالح'
            })

    except Exception as e:
        print(f"Verification error: {str(e)}")
        return render(request, 'error.html', {
            'message': 'حدث خطأ أثناء تفعيل الحساب'
        })

@api_view(['POST'])
def test(request):
    print("تم استلام الطلب:")
    print("البيانات المستلمة:", request.data)
    return Response({
        'success': True,
        'received_data': request.data,
        'message': 'تم استلام البيانات بنجاح'
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTokenValid])
def profile_view(request):
    """عرض معلومات الملف الشخصي"""
    return Response({
        'id': request.user.id,
        'email': request.user.email,
        'full_name': request.user.full_name,
        'profile_image': request.user.profile_image.url if request.user.profile_image else None
    })

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer])
def update_profile(request):
    """تحديث اسم المستخدم"""
    try:
        user = request.user
        
        if 'full_name' not in request.data:
            return Response({
                'success': False,
                'error': 'يجب توفير الاسم الكامل'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.full_name = request.data['full_name']
        user.save()
        
        return Response({
            'success': True,
            'message': 'تم تحديث الاسم بنجاح',
            'full_name': user.full_name
        })
    except Exception as e:
        print(f"Error in update_profile: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer])
def change_password(request):
    try:
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not old_password or not new_password:
            return Response({
                'success': False,
                'error': 'يرجى توفير كلمة المرور القديمة والجديدة'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if not user.check_password(old_password):
            return Response({
                'success': False,
                'error': 'كلمة المرور القديمة غير صحيحة'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        user.set_password(new_password)
        user.save()
        
        return Response({
            'success': True,
            'message': 'تم تغيير كلمة المرور بنجاح'
        })
    except Exception as e:
        print(f"خطأ في change_password: {str(e)}")
        return Response({
            'success': False,
            'error': 'حدث خطأ أثناء تغيير كلمة المرور'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account(request):
    """حذف الحساب"""
    try:
        request.user.delete()
        return Response({
            'message': 'تم حذف الحساب بنجاح'
        })
    except Exception as e:
        return Response({
            'error': 'حدث خطأ أثناء حذف الحساب'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get('refresh')
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({
            'success': True,
            'message': 'تم تسجيل الخروج بنجاح'
        })
    except Exception as e:
        print(f"Logout error: {str(e)}")
        return Response({
            'success': False,
            'message': 'حدث خطأ أثناء تسجيل الخروج'
        }, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def update_profile_image(request):
    """تحديث صورة الملف الشخصي"""
    try:
        user = request.user
        
        if 'image' not in request.FILES:
            return Response({
                'error': 'يرجى اختيار صورة لرفعها'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        image = request.FILES['image']
        
        # التحقق من نوع الملف
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg']
        if image.content_type not in allowed_types:
            return Response({
                'error': 'يرجى اختيار صورة بصيغة JPG أو PNG فقط'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # التحقق من حجم الصورة (مثلاً 5 ميجابايت كحد أقصى)
        if image.size > 5 * 1024 * 1024:  # 5MB
            return Response({
                'error': 'حجم الصورة يجب أن لا يتجاوز 5 ميجابايت'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # حذف الصورة القديمة إذا وجدت
        if user.profile_image:
            user.profile_image.delete()
            
        # حفظ الصورة الجديدة
        user.profile_image = image
        user.save()
        
        return Response({
            'message': 'تم تحديث صورة الملف الشخصي بنجاح',
            'image_url': request.build_absolute_uri(user.profile_image.url)
        })
        
    except Exception as e:
        return Response({
            'error': 'حدث خطأ أثناء تحديث صورة الملف الشخصي'
        }, status=status.HTTP_400_BAD_REQUEST)

def generate_token(user):
    """إنشاء توكن جديد"""
    try:
        refresh = RefreshToken.for_user(user)
        
        # نرجع التوكنات فقط دون تسجيلها في قاعدة البيانات
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }
    except Exception as e:
        print(f"Error in generate_token: {str(e)}")
        return None

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    try:
        user = request.user
        return Response({
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'profile_image': user.profile_image.url if user.profile_image else None
            }
        })
    except Exception as e:
        print(f"خطأ في profile: {str(e)}")
        return Response({
            'success': False,
            'error': 'حدث خطأ أثناء جلب بيانات الملف الشخصي'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def refresh_token(request):
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({
                'success': False,
                'message': 'يجب توفير رمز التحديث'
            }, status=400)
            
        token = RefreshToken(refresh_token)
        access_token = str(token.access_token)
        
        return Response({
            'success': True,
            'access': access_token
        })
    except Exception as e:
        print(f"Refresh token error: {str(e)}")
        return Response({
            'success': False,
            'message': 'رمز التحديث غير صالح'
        }, status=400)
