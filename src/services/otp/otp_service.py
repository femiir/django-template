import secrets

from django.shortcuts import get_object_or_404
from otp.models import Otp, OtpType

def generate_otp_code(length=6):
    """Generate a secure numeric OTP code of given length."""
    return ''.join(str(secrets.randbelow(10)) for _ in range(length))


def create_otp(user, otp_type: OtpType):
    """Create a new OTP for the user."""
    otp_code = generate_otp_code()
    otp = Otp.objects.create(
        user=user,
        otp_code=otp_code,
        otp_type=otp_type,
    )
    return otp


def verify_otp(user, otp_code: str, otp_type: OtpType):
    """Verify the provided OTP code for the user."""
    otp = get_object_or_404(Otp, user=user, otp_code=otp_code, otp_type=otp_type, is_used=False)

    if otp.is_used or otp.is_expired():
        return False, "OTP is either used or expired."
    
    otp.mark_as_used()
    return True, "OTP is validated."