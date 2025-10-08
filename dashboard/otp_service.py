"""
OTP Service for generating, validating, and managing OTP codes
"""
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import OTP, UserProfile
import logging

logger = logging.getLogger(__name__)


class OTPService:
    """Service class for OTP operations"""
    
    OTP_EXPIRY_MINUTES = 5  # OTP expires after 5 minutes
    MAX_OTP_ATTEMPTS = 3    # Maximum OTP attempts per hour
    
    @classmethod
    def generate_otp(cls, user, phone_number, purpose='login'):
        """
        Generate a new OTP for the user
        
        Args:
            user: Django User instance
            phone_number: Phone number to send OTP to
            purpose: Purpose of OTP (login, reset_password, verify_phone)
            
        Returns:
            OTP instance or None if generation failed
        """
        try:
            # Clean up expired OTPs for this user
            cls._cleanup_expired_otps(user)
            
            # Check if user has exceeded OTP attempts
            if not cls._check_otp_rate_limit(user):
                logger.warning(f"User {user.username} exceeded OTP rate limit")
                return None
            
            # Generate new OTP code
            code = OTP.generate_code()
            expires_at = timezone.now() + timedelta(minutes=cls.OTP_EXPIRY_MINUTES)
            
            # Create OTP instance
            otp = OTP.objects.create(
                user=user,
                code=code,
                phone_number=phone_number,
                expires_at=expires_at,
                purpose=purpose
            )
            
            logger.info(f"Generated OTP for user {user.username}")
            return otp
            
        except Exception as e:
            logger.error(f"Failed to generate OTP for user {user.username}: {str(e)}")
            return None
    
    @classmethod
    def validate_otp(cls, user, code, phone_number=None, purpose='login'):
        """
        Validate an OTP code
        
        Args:
            user: Django User instance
            code: OTP code to validate
            phone_number: Phone number (optional, for additional validation)
            purpose: Purpose of OTP
            
        Returns:
            OTP instance if valid, None otherwise
        """
        try:
            # Find the most recent valid OTP for this user
            otp = OTP.objects.filter(
                user=user,
                code=code,
                purpose=purpose,
                is_used=False
            ).order_by('-created_at').first()
            
            if not otp:
                logger.warning(f"No valid OTP found for user {user.username}")
                return None
            
            # Check if OTP has expired
            if otp.is_expired():
                logger.warning(f"OTP expired for user {user.username}")
                return None
            
            # Additional phone number validation if provided
            if phone_number and otp.phone_number != phone_number:
                logger.warning(f"Phone number mismatch for user {user.username}")
                return None
            
            # Mark OTP as used
            otp.mark_as_used()
            logger.info(f"OTP validated successfully for user {user.username}")
            return otp
            
        except Exception as e:
            logger.error(f"Failed to validate OTP for user {user.username}: {str(e)}")
            return None
    
    @classmethod
    def send_otp_sms(cls, otp):
        """
        Send OTP via SMS
        
        Args:
            otp: OTP instance
            
        Returns:
            bool: True if SMS sent successfully, False otherwise
        """
        try:
            from .sms_service import send_otp_sms
            
            return send_otp_sms(otp.phone_number, otp.code, language='ar')
            
        except Exception as e:
            logger.error(f"Failed to send SMS for OTP {otp.id}: {str(e)}")
            return False
    
    @classmethod
    def get_user_by_phone(cls, phone_number):
        """
        Get user by phone number
        
        Args:
            phone_number: Phone number to search for
            
        Returns:
            User instance or None if not found
        """
        try:
            profile = UserProfile.objects.filter(phone_number=phone_number).first()
            return profile.user if profile else None
        except Exception as e:
            logger.error(f"Failed to get user by phone {phone_number}: {str(e)}")
            return None
    
    @classmethod
    def _cleanup_expired_otps(cls, user):
        """Clean up expired OTPs for a user"""
        try:
            OTP.objects.filter(
                user=user,
                expires_at__lt=timezone.now()
            ).delete()
        except Exception as e:
            logger.error(f"Failed to cleanup expired OTPs for user {user.username}: {str(e)}")
    
    @classmethod
    def _check_otp_rate_limit(cls, user):
        """
        Check if user has exceeded OTP rate limit
        
        Args:
            user: Django User instance
            
        Returns:
            bool: True if within rate limit, False otherwise
        """
        try:
            # Count OTPs generated in the last hour
            one_hour_ago = timezone.now() - timedelta(hours=1)
            otp_count = OTP.objects.filter(
                user=user,
                created_at__gte=one_hour_ago
            ).count()
            
            return otp_count < cls.MAX_OTP_ATTEMPTS
            
        except Exception as e:
            logger.error(f"Failed to check rate limit for user {user.username}: {str(e)}")
            return False
    
    @classmethod
    def get_otp_for_user(cls, user, purpose='login'):
        """
        Get the latest valid OTP for a user
        
        Args:
            user: Django User instance
            purpose: Purpose of OTP
            
        Returns:
            OTP instance or None if not found
        """
        try:
            return OTP.objects.filter(
                user=user,
                purpose=purpose,
                is_used=False,
                expires_at__gt=timezone.now()
            ).order_by('-created_at').first()
        except Exception as e:
            logger.error(f"Failed to get OTP for user {user.username}: {str(e)}")
            return None
