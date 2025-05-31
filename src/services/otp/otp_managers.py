import secrets
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