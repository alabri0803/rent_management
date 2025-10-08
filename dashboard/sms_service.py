"""
SMS Service for sending OTP codes
This is a placeholder implementation that can be extended with actual SMS providers
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class SMSService:
    """
    SMS Service for sending OTP codes
    Supports multiple SMS providers (Twilio, AWS SNS, etc.)
    """
    
    def __init__(self):
        self.provider = getattr(settings, 'SMS_PROVIDER', 'console')  # Default to console for development
    
    def send_sms(self, phone_number, message):
        """
        Send SMS message
        
        Args:
            phone_number: Recipient's phone number
            message: SMS message content
            
        Returns:
            bool: True if SMS sent successfully, False otherwise
        """
        try:
            if self.provider == 'twilio':
                return self._send_via_twilio(phone_number, message)
            elif self.provider == 'aws_sns':
                return self._send_via_aws_sns(phone_number, message)
            elif self.provider == 'console':
                return self._send_via_console(phone_number, message)
            else:
                logger.error(f"Unknown SMS provider: {self.provider}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone_number}: {str(e)}")
            return False
    
    def _send_via_console(self, phone_number, message):
        """
        Send SMS via console (for development/testing)
        """
        logger.info(f"SMS to {phone_number}: {message}")
        print(f"\n{'='*50}")
        print(f"SMS TO: {phone_number}")
        print(f"MESSAGE: {message}")
        print(f"{'='*50}\n")
        return True
    
    def _send_via_twilio(self, phone_number, message):
        """
        Send SMS via Twilio
        
        Required settings:
        - TWILIO_ACCOUNT_SID
        - TWILIO_AUTH_TOKEN
        - TWILIO_PHONE_NUMBER
        """
        try:
            from twilio.rest import Client
            
            account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
            auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
            from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', None)
            
            if not all([account_sid, auth_token, from_number]):
                logger.error("Twilio credentials not configured")
                return False
            
            client = Client(account_sid, auth_token)
            
            message = client.messages.create(
                body=message,
                from_=from_number,
                to=phone_number
            )
            
            logger.info(f"Twilio SMS sent successfully. SID: {message.sid}")
            return True
            
        except ImportError:
            logger.error("Twilio library not installed. Install with: pip install twilio")
            return False
        except Exception as e:
            logger.error(f"Twilio SMS failed: {str(e)}")
            return False
    
    def _send_via_aws_sns(self, phone_number, message):
        """
        Send SMS via AWS SNS
        
        Required settings:
        - AWS_ACCESS_KEY_ID
        - AWS_SECRET_ACCESS_KEY
        - AWS_SNS_REGION
        """
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            region = getattr(settings, 'AWS_SNS_REGION', 'us-east-1')
            
            sns_client = boto3.client(
                'sns',
                region_name=region,
                aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
                aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
            )
            
            response = sns_client.publish(
                PhoneNumber=phone_number,
                Message=message
            )
            
            logger.info(f"AWS SNS SMS sent successfully. MessageId: {response['MessageId']}")
            return True
            
        except ImportError:
            logger.error("boto3 library not installed. Install with: pip install boto3")
            return False
        except ClientError as e:
            logger.error(f"AWS SNS SMS failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"AWS SNS SMS failed: {str(e)}")
            return False


# Global SMS service instance
sms_service = SMSService()


def send_otp_sms(phone_number, otp_code, language='ar'):
    """
    Send OTP SMS message
    
    Args:
        phone_number: Recipient's phone number
        otp_code: OTP code to send
        language: Language for the message ('ar' or 'en')
        
    Returns:
        bool: True if SMS sent successfully, False otherwise
    """
    if language == 'ar':
        message = f"رمز التحقق الخاص بك هو: {otp_code}. صالح لمدة 5 دقائق."
    else:
        message = f"Your verification code is: {otp_code}. Valid for 5 minutes."
    
    return sms_service.send_sms(phone_number, message)
