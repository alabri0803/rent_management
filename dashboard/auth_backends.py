"""
Custom authentication backends for OTP and enhanced authentication
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q
from .otp_service import OTPService
import logging

logger = logging.getLogger(__name__)


class OTPSMSBackend(ModelBackend):
    """
    Authentication backend for OTP via SMS
    """
    
    def authenticate(self, request, phone_number=None, otp_code=None, **kwargs):
        """
        Authenticate user using phone number and OTP code
        
        Args:
            request: Django request object
            phone_number: User's phone number
            otp_code: OTP code entered by user
            
        Returns:
            User instance if authentication successful, None otherwise
        """
        if not phone_number or not otp_code:
            return None
        
        try:
            # Get user by phone number
            user = OTPService.get_user_by_phone(phone_number)
            if not user:
                logger.warning(f"No user found with phone number: {phone_number}")
                return None
            
            # Validate OTP
            otp = OTPService.validate_otp(user, otp_code, phone_number, purpose='login')
            if not otp:
                logger.warning(f"Invalid OTP for user: {user.username}")
                return None
            
            # Check if user account is active
            if not self.user_can_authenticate(user):
                logger.warning(f"User {user.username} cannot authenticate (inactive)")
                return None
            
            logger.info(f"OTP authentication successful for user: {user.username}")
            return user
            
        except Exception as e:
            logger.error(f"OTP authentication error: {str(e)}")
            return None
    
    def get_user(self, user_id):
        """
        Get user by ID
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class EmailUsernameBackend(ModelBackend):
    """
    Enhanced authentication backend that allows login with email or username
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user using email or username
        
        Args:
            request: Django request object
            username: Username or email address
            password: User's password
            
        Returns:
            User instance if authentication successful, None otherwise
        """
        if not username or not password:
            return None
        
        try:
            # Try to find user by username or email
            user = User.objects.filter(
                Q(username=username) | Q(email=username)
            ).first()
            
            if not user:
                logger.warning(f"No user found with username/email: {username}")
                return None
            
            # Check password
            if not user.check_password(password):
                logger.warning(f"Invalid password for user: {user.username}")
                return None
            
            # Check if user account is active
            if not self.user_can_authenticate(user):
                logger.warning(f"User {user.username} cannot authenticate (inactive)")
                return None
            
            logger.info(f"Password authentication successful for user: {user.username}")
            return user
            
        except Exception as e:
            logger.error(f"Password authentication error: {str(e)}")
            return None
    
    def get_user(self, user_id):
        """
        Get user by ID
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
