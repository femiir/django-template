import secrets

def generate_otp_code(length=6):
    """Generate a secure numeric OTP code of given length."""
    return ''.join(str(secrets.randbelow(10)) for _ in range(length))