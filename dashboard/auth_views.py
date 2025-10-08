"""
Enhanced authentication views supporting both password and OTP login
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
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from .otp_service import OTPService
import logging

logger = logging.getLogger(__name__)


class EnhancedLoginView(LoginView):
    """
    Enhanced login view that supports both password and OTP authentication
    """
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['show_otp_option'] = True
        return context
    
    def post(self, request, *args, **kwargs):
        """
        Handle both password and OTP login
        """
        login_method = request.POST.get('login_method', 'password')
        
        if login_method == 'otp':
            return self._handle_otp_login(request)
        else:
            return self._handle_password_login(request)
    
    def _handle_password_login(self, request):
        """
        Handle traditional password login
        """
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        remember_me = request.POST.get('remember', False)
        
        if not username or not password:
            messages.error(request, _('اسم المستخدم وكلمة المرور مطلوبان'))
            return self.render_to_response(self.get_context_data())
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Handle remember me functionality
            if not remember_me:
                request.session.set_expiry(0)  # Session expires when browser closes
            
            # Redirect based on user type
            if user.is_staff:
                return redirect('/dashboard/')
            else:
                return redirect('/portal/')
        else:
            messages.error(request, _('اسم المستخدم أو كلمة المرور غير صحيحة'))
            return self.render_to_response(self.get_context_data())
    
    def _handle_otp_login(self, request):
        """
        Handle OTP login
        """
        phone_number = request.POST.get('phone_number', '').strip()
        if not phone_number.startswith('+968') or len(phone_number) != 12 or not phone_number[1:].isdigit():
            messages.error(request, _('يرجى إدخال رقم هاتف عماني يبدأ بـ +968 ويتبعه 8 أرقام'))
            return self.render_to_response(self.get_context_data())
        otp_code = request.POST.get('otp_code', '').strip()
        
        if not phone_number:
            messages.error(request, _('رقم الهاتف مطلوب'))
            return self.render_to_response(self.get_context_data())
        
        if not otp_code:
            messages.error(request, _('رمز التحقق مطلوب'))
            return self.render_to_response(self.get_context_data())
        
        # Authenticate user using OTP
        user = authenticate(
            request,
            phone_number=phone_number,
            otp_code=otp_code
        )
        
        if user is not None:
            login(request, user)
            
            # Redirect based on user type
            if user.is_staff:
                return redirect('/dashboard/')
            else:
                return redirect('/portal/')
        else:
            messages.error(request, _('رمز التحقق غير صحيح أو منتهي الصلاحية'))
            return self.render_to_response(self.get_context_data())


@csrf_exempt
@require_POST
@never_cache
def send_login_otp(request):
    """
    Send OTP for login (AJAX endpoint)
    """
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
        logger.error(f"Error sending login OTP: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': _('حدث خطأ. حاول مرة أخرى')
        })


@csrf_exempt
@require_POST
@never_cache
def verify_login_otp(request):
    """
    Verify OTP for login (AJAX endpoint)
    """
    phone_number = request.POST.get('phone_number', '').strip()
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
        logger.error(f"Error verifying login OTP: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': _('حدث خطأ. حاول مرة أخرى')
        })


@login_required
def user_profile(request):
    """
    User profile page with phone number management
    """
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = None
    
    context = {
        'profile': profile,
        'user': request.user
    }
    
    return render(request, 'dashboard/profile.html', context)
