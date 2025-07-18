import logging
from typing import Optional

from django.conf import settings
from twilio.rest import Client
from twilio.base.exceptions import TwilioException

logger = logging.getLogger(__name__)


class TwilioSMSService:
    """
    Service for sending SMS messages using Twilio.
    """
    
    def __init__(self):
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        self.from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', None)
        
        if not all([self.account_sid, self.auth_token, self.from_number]):
            logger.error("Twilio credentials not properly configured")
            raise ValueError("Twilio credentials missing from settings")
            
        self.client = Client(self.account_sid, self.auth_token)
    
    def send_sms(
        self,
        to_number: str,
        message: str,
        from_number: Optional[str] = None
    ) -> dict:
        """
        Send an SMS message using Twilio.
        
        Args:
            to_number: Recipient phone number (e.g., "+1234567890")
            message: SMS message content
            from_number: Sender phone number (optional, uses default if not provided)
            
        Returns:
            dict: Response containing success status and message details
        """
        try:
            
            sender = from_number or self.from_number
            message_instance = self.client.messages.create(
                body=message,
                from_=sender,
                to=to_number
            )
            
            logger.info(f"SMS sent successfully to {to_number}. SID: {message_instance.sid}")
            
            return {
                'success': True,
                'sid': message_instance.sid,
                'status': message_instance.status,
                'to': to_number,
                'from': sender,
                'message': message,
                'error': None
            }
            
        except TwilioException as e:
            logger.error(f"Twilio error sending SMS to {to_number}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'sid': None,
                'to': to_number,
                'message': message
            }
        except Exception as e:
            logger.error(f"Unexpected error sending SMS to {to_number}: {str(e)}")
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'sid': None,
                'to': to_number,
                'message': message
            }
