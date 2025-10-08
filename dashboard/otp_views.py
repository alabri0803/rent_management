"""
Views for OTP authentication functionality
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.translation import gettext as _
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.cache import never_cache
from .models import UserProfile
from .otp_service import OTPService
import logging

logger = logging.getLogger(__name__)


@never_cache
def send_otp_view(request):
    """
    Send OTP to user's phone number
    """
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '').strip()
        if not phone_number.startswith('+968') or len(phone_number) != 12 or not phone_number[1:].isdigit():
            return JsonResponse({'success': False, 'message': _('يرجى إدخال رقم هاتف عماني يبدأ بـ +968 ويتبعه 8 أرقام')})
        
        if not phone_number:
            return JsonResponse({
                'success': False,
                'message': _('رقم الهاتف مطلوب')
            })
        
        try:
            # Get user by phone number
            user = OTPService.get_user_by_phone(phone_number)
            if not user:
                return JsonResponse({
                    'success': False,
                    'message': _('لا يوجد مستخدم مسجل بهذا الرقم')
                })
            
            # Generate OTP
            otp = OTPService.generate_otp(user, phone_number, purpose='login')
            if not otp:
                return JsonResponse({
                    'success': False,
                    'message': _('تم تجاوز الحد المسموح من محاولات إرسال الرمز. حاول مرة أخرى لاحقاً')
                })
            
            # Send SMS
            sms_sent = OTPService.send_otp_sms(otp)
            if not sms_sent:
                return JsonResponse({
                    'success': False,
                    'message': _('فشل في إرسال الرسالة. حاول مرة أخرى')
                })
            
            return JsonResponse({
                'success': True,
                'message': _('تم إرسال رمز التحقق إلى رقم هاتفك')
            })
            
        except Exception as e:
            logger.error(f"Error sending OTP: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': _('حدث خطأ. حاول مرة أخرى')
            })
    
    return JsonResponse({
        'success': False,
        'message': _('طريقة غير صحيحة')
    })


@never_cache
def verify_otp_view(request):
    """
    Verify OTP and authenticate user
    """
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '').strip()
        if not phone_number.startswith('+968') or len(phone_number) != 12 or not phone_number[1:].isdigit():
            return JsonResponse({'success': False, 'message': _('يرجى إدخال رقم هاتف عماني يبدأ بـ +968 ويتبعه 8 أرقام')})
        otp_code = request.POST.get('otp_code', '').strip()
        
        if not phone_number or not otp_code:
            return JsonResponse({
                'success': False,
                'message': _('رقم الهاتف ورمز التحقق مطلوبان')
            })
        
        try:
            # Authenticate user using OTP
            user = authenticate(
                request,
                phone_number=phone_number,
                otp_code=otp_code
            )
            
            if user:
                # Login user
                login(request, user)
                
                # Redirect based on user type
                if user.is_staff:
                    redirect_url = '/dashboard/'
                else:
                    redirect_url = '/portal/'
                
                return JsonResponse({
                    'success': True,
                    'message': _('تم تسجيل الدخول بنجاح'),
                    'redirect_url': redirect_url
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': _('رمز التحقق غير صحيح أو منتهي الصلاحية')
                })
                
        except Exception as e:
            logger.error(f"Error verifying OTP: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': _('حدث خطأ. حاول مرة أخرى')
            })
    
    return JsonResponse({
        'success': False,
        'message': _('طريقة غير صحيحة')
    })


@login_required
def setup_phone_number(request):
    """
    Setup phone number for OTP authentication
    """
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '').strip()
        
        if not phone_number:
            messages.error(request, _('رقم الهاتف مطلوب'))
            return redirect('setup_phone')
        
        try:
            # Create or update user profile
            profile, created = UserProfile.objects.get_or_create(
                user=request.user,
                defaults={'phone_number': phone_number}
            )
            
            if not created:
                profile.phone_number = phone_number
                profile.save()
            
            messages.success(request, _('تم حفظ رقم الهاتف بنجاح'))
            return redirect('profile')
            
        except Exception as e:
            logger.error(f"Error setting up phone number: {str(e)}")
            messages.error(request, _('حدث خطأ. حاول مرة أخرى'))
    
    return render(request, 'dashboard/setup_phone.html')


@login_required
def verify_phone_number(request):
    """
    Verify phone number by sending OTP
    """
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code', '').strip()
        
        if not otp_code:
            messages.error(request, _('رمز التحقق مطلوب'))
            return redirect('verify_phone')
        
        try:
            profile = request.user.profile
            if not profile or not profile.phone_number:
                messages.error(request, _('لم يتم العثور على رقم هاتف'))
                return redirect('setup_phone')
            
            # Verify OTP
            otp = OTPService.validate_otp(
                request.user,
                otp_code,
                profile.phone_number,
                purpose='verify_phone'
            )
            
            if otp:
                messages.success(request, _('تم التحقق من رقم الهاتف بنجاح'))
                return redirect('profile')
            else:
                messages.error(request, _('رمز التحقق غير صحيح'))
                
        except Exception as e:
            logger.error(f"Error verifying phone number: {str(e)}")
            messages.error(request, _('حدث خطأ. حاول مرة أخرى'))
    
    return render(request, 'dashboard/verify_phone.html')


@login_required
def send_phone_verification_otp(request):
    """
    Send OTP for phone number verification
    """
    if request.method == 'POST':
        try:
            profile = request.user.profile
            if not profile or not profile.phone_number:
                return JsonResponse({
                    'success': False,
                    'message': _('لم يتم العثور على رقم هاتف')
                })
            
            # Generate OTP for phone verification
            otp = OTPService.generate_otp(
                request.user,
                profile.phone_number,
                purpose='verify_phone'
            )
            
            if not otp:
                return JsonResponse({
                    'success': False,
                    'message': _('تم تجاوز الحد المسموح من محاولات إرسال الرمز')
                })
            
            # Send SMS
            sms_sent = OTPService.send_otp_sms(otp)
            if not sms_sent:
                return JsonResponse({
                    'success': False,
                    'message': _('فشل في إرسال الرسالة')
                })
            
            return JsonResponse({
                'success': True,
                'message': _('تم إرسال رمز التحقق إلى رقم هاتفك')
            })
            
        except Exception as e:
            logger.error(f"Error sending phone verification OTP: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': _('حدث خطأ. حاول مرة أخرى')
            })
    
    return JsonResponse({
        'success': False,
        'message': _('طريقة غير صحيحة')
    })
