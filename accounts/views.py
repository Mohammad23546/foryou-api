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
        print("Received registration data:", request.data)
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.set_password(request.data['password'])
            user.is_active = False  # جعل الحساب غير مفعل عند التسجيل
            user.save()
            
            token = generate_verification_token(user)
            verification_url = f"https://foryou-api.onrender.com/api/auth/verify-email/?token={token}"
            email_sent = send_verification_email(user, token)
            
            return Response({
                'success': True,
                'message': 'تم إنشاء الحساب بنجاح. يرجى التحقق من بريدك الإلكتروني لتفعيل الحساب.',
                'verification_url': verification_url
            })
        else:
            print("Validation errors:", serializer.errors)  # لطباعة أخطاء التحقق
            return Response({
                'success': False,
                'message': 'بيانات غير صالحة',
                'errors': serializer.errors
            }, status=400)
            
    except Exception as e:
        print(f"Registration error: {str(e)}")  # لطباعة أي أخطاء أخرى
        return Response({
            'success': False,
            'message': f'حدث خطأ أثناء التسجيل: {str(e)}'
        }, status=500)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    try:
        print("=== بداية طلب تسجيل الدخول ===")
        data = request.data
        print("البيانات المستلمة:", data)
        
        email = data.get('email')
        password = data.get('password')
        print(f"البريد الإلكتروني: {email}")
        print("كلمة المرور: ***********")
        
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
            print(f"تم العثور على المستخدم: {user.email}")
            
            if user.check_password(password):
                if user.is_active:  # نتحقق فقط من is_active
                    refresh = RefreshToken.for_user(user)
                    return Response({
                        'success': True,
                        'token': str(refresh.access_token),
                        'refresh': str(refresh),
                        'user': {
                            'id': user.id,
                            'email': user.email,
                            'username': user.username
                        }
                    })
                else:
                    # إذا لم يكن الحساب مفعلاً
                    token = generate_verification_token(user)
                    send_verification_email(user, token)
                    return Response({
                        'success': False,
                        'error': 'حسابك غير مفعل! يرجى مراجعة بريدك الإلكتروني لتفعيل حسابك',
                        'requires_activation': True,
                        'duration': 5000
                    }, status=401)
            
        except User.DoesNotExist:
            print(f"لم يتم العثور على مستخدم بالبريد: {email}")
            
        return Response({
            'success': False,
            'error': 'البريد الإلكتروني أو كلمة المرور غير صحيحة'
        }, status=401)
        
    except Exception as e:
        print(f"خطأ في تسجيل الدخول: {str(e)}")
        return Response({
            'success': False,
            'error': 'حدث خطأ أثناء تسجيل الدخول'
        }, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email(request):
    try:
        token = request.GET.get('token')
        print(f"Received verification token: {token}")  # تتبع التوكن المستلم
        
        if not token:
            print("No token provided")
            return render(request, 'error.html', {
                'message': 'رمز التحقق غير صالح'
            })

        try:
            # فك تشفير التوكن
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
            print(f"Decoded token payload: {payload}")  # تتبع محتوى التوكن
            
            if not user_id:
                print("No user_id in token")
                return render(request, 'error.html', {
                    'message': 'رمز التحقق غير صالح'
                })
                
            # البحث عن المستخدم
            User = get_user_model()
            user = User.objects.get(id=user_id)
            print(f"Found user: {user.email}")  # تتبع المستخدم
            
            # تفعيل الحساب
            print(f"Before activation - is_active: {user.is_active}")  # حالة قبل التفعيل
            user.is_active = True
            user.save()
            print(f"After activation - is_active: {user.is_active}")  # حالة بعد التفعيل
            
            return render(request, 'email_verification_success.html', {
                'message': 'تم تفعيل حسابك بنجاح! يمكنك الآن تسجيل الدخول.'
            })
            
        except jwt.ExpiredSignatureError:
            print("Token expired")
            return render(request, 'error.html', {
                'message': 'انتهت صلاحية رمز التحقق'
            })
        except jwt.InvalidTokenError:
            print("Invalid token")
            return render(request, 'error.html', {
                'message': 'رمز التحقق غير صالح'
            })
        except User.DoesNotExist:
            print(f"User with id {user_id} not found")
            return render(request, 'error.html', {
                'message': 'المستخدم غير موجود'
            })
            
    except Exception as e:
        print(f"Verification error: {str(e)}")
        return render(request, 'error.html', {
            'message': 'حدث خطأ أثناء التحقق'
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
