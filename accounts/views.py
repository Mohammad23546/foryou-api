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
from .utils import send_verification_email
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
        print("=== بداية طلب التسجيل ===")
        print(f"نوع الطلب: {request.method}")
        print(f"المسار: {request.path}")
        print(f"نوع المحتوى: {request.content_type}")
        print(f"الرؤوس: {request.headers}")
        print(f"البيانات الخام: {request.body}")
        print(f"البيانات المعالجة: {request.data}")
        
        email = request.data.get('email', '').strip()
        full_name = request.data.get('full_name', '').strip()
        password = request.data.get('password', '').strip()
        
        print(f"البريد: {email}")
        print(f"الاسم: {full_name}")
        print(f"كلمة المرور: {'*' * len(password)}")
        
        # التحقق من وجود المستخدم
        if User.objects.filter(email=email).exists():
            return Response({
                'success': False,
                'error': 'البريد الإلكتروني مسجل مسبقاً',
                'duration': 5000  # مدة ظهور الرسالة بالميلي ثانية
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # إنشاء المستخدم
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            full_name=full_name
        )
        
        # إنشاء توكن التحقق
        token = uuid.uuid4()
        EmailVerification.objects.create(
            user=user,
            token=token
        )
        
        # إرسال بريد التحقق
        if send_verification_email(user, token):
            # إنشاء توكن JWT
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'success': True,
                'message': 'تم إنشاء الحساب بنجاح! يرجى تفعيل حسابك من خلال الرابط المرسل إلى بريدك الإلكتروني',
                'duration': 5000,  # مدة ظهور الرسالة بالميلي ثانية
                'token': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                },
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'profile_image': user.profile_image.url if user.profile_image else None
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'error': 'تم إنشاء الحساب ولكن فشل إرسال بريد التفعيل. يرجى المحاولة مرة أخرى',
                'duration': 5000
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        print(f"Error in register: {str(e)}")
        return Response({
            'success': False,
            'error': 'حدث خطأ أثناء إنشاء الحساب',
            'duration': 5000
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    try:
        print("\n=== بداية طلب تسجيل الدخول ===")
        print(f"البيانات المستلمة: {request.data}")
        
        # التحقق من وجود البيانات المطلوبة
        if not request.data:
            print("خطأ: لا توجد بيانات مرسلة")
            return Response({
                'success': False,
                'error': 'يرجى إدخال البريد الإلكتروني وكلمة المرور',
                'duration': 5000
            }, status=status.HTTP_400_BAD_REQUEST)

        email = request.data.get('email')
        password = request.data.get('password')
        
        print(f"البريد الإلكتروني: {email}")
        print(f"كلمة المرور: {'*' * len(password) if password else None}")

        # التحقق من إدخال البريد الإلكتروني وكلمة المرور
        if not email or not password:
            print("خطأ: البريد الإلكتروني أو كلمة المرور غير موجودة")
            return Response({
                'success': False,
                'error': 'يرجى إدخال البريد الإلكتروني وكلمة المرور',
                'duration': 5000
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            print(f"تم العثور على المستخدم: {user.email}")
            
            # التحقق من كلمة المرور
            if not user.check_password(password):
                print("خطأ: كلمة المرور غير صحيحة")
                return Response({
                    'success': False,
                    'error': 'كلمة المرور غير صحيحة',
                    'duration': 5000
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # التحقق من تفعيل الحساب
            verification = EmailVerification.objects.filter(user=user).first()
            print(f"حالة التحقق: {verification.is_verified if verification else 'لا يوجد تحقق'}")
            
            # إذا لم يكن هناك سجل تحقق أو الحساب غير مفعل
            if not verification or not verification.is_verified:
                # إذا لم يكن هناك سجل تحقق، نقوم بإنشاء واحد
                if not verification:
                    print("إنشاء سجل تحقق جديد")
                    token = uuid.uuid4()
                    verification = EmailVerification.objects.create(
                        user=user,
                        token=token,
                        is_verified=False
                    )
                
                # إرسال رابط التفعيل
                print("إرسال رابط التفعيل")
                send_verification_email(user, verification.token)
                
                response_data = {
                    'success': False,
                    'error': 'حسابك غير مفعل! يرجى مراجعة بريدك الإلكتروني لتفعيل حسابك',
                    'requires_activation': True,
                    'duration': 5000
                }
                print(f"إرسال رد: {response_data}")
                return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)
            
            # إذا كل شيء صحيح، نقوم بتسجيل الدخول
            print("تسجيل الدخول بنجاح")
            refresh = RefreshToken.for_user(user)
            
            response_data = {
                'success': True,
                'message': 'تم تسجيل الدخول بنجاح',
                'duration': 3000,
                'token': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                },
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'profile_image': user.profile_image.url if user.profile_image else None
                }
            }
            print(f"إرسال رد: {response_data}")
            return Response(response_data)
            
        except User.DoesNotExist:
            print(f"خطأ: لم يتم العثور على مستخدم بالبريد {email}")
            return Response({
                'success': False,
                'error': 'البريد الإلكتروني غير مسجل',
                'should_register': True,
                'duration': 5000
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except Exception as e:
        print(f"خطأ غير متوقع: {str(e)}")
        return Response({
            'success': False,
            'error': 'حدث خطأ أثناء تسجيل الدخول. يرجى المحاولة مرة أخرى',
            'duration': 5000
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email(request, token):
    try:
        print("\n=== تفاصيل طلب التحقق من البريد ===")
        print(f"Token: {token}")
        
        # تحويل التوكن إلى UUID
        token_uuid = uuid.UUID(token)
        print(f"UUID Token: {token_uuid}")
        
        # البحث عن التحقق
        verification = EmailVerification.objects.get(token=token_uuid)
        print(f"User: {verification.user.email}")
        print(f"Current verification status: {verification.is_verified}")
        
        if verification.is_verified:
            return render(request, 'email_verification_success.html', {
                'message': 'تم تفعيل حسابك مسبقاً'
            })
        
        # تفعيل الحساب
        verification.is_verified = True
        verification.save()
        print(f"New verification status: {verification.is_verified}")
        
        return render(request, 'email_verification_success.html', {
            'message': 'تم تفعيل حسابك بنجاح'
        })
        
    except (ValueError, EmailVerification.DoesNotExist) as e:
        print(f"Error: {str(e)}")
        return render(request, 'error.html', {
            'error': 'رابط التفعيل غير صالح'
        })
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return render(request, 'error.html', {
            'error': 'حدث خطأ أثناء تفعيل الحساب'
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
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({
                'success': True,
                'message': 'تم تسجيل الخروج بنجاح'
            })
        return Response({
            'success': False,
            'error': 'لم يتم توفير توكن التحديث'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(f"خطأ في logout: {str(e)}")
        return Response({
            'success': False,
            'error': 'حدث خطأ أثناء تسجيل الخروج'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
