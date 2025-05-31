from ninja import Router

from accounts.models import User
from otp.models import Otp
from otp.schema.otp import OtpValidateIn, OtpValidateOut

otp_router = Router(tags=['OTP'])


@otp_router.post('/validate/', response=OtpValidateOut)
def validate_otp(request, payload: OtpValidateIn):
	try:
		user = User.objects.get(email=payload.email)
	except User.DoesNotExist:
		return OtpValidateOut(success=False, message='User not found.')

	try:
		otp = Otp.objects.get(
			user=user,
			otp_code=payload.otp_code,
			otp_type=payload.otp_type,
			is_used=False,
		)
	except Otp.DoesNotExist:
		return OtpValidateOut(success=False, message='Invalid or already used OTP.')

	if otp.is_expired():
		return OtpValidateOut(success=False, message='OTP has expired.')

	otp.mark_as_used()
	return OtpValidateOut(success=True, message='OTP validated successfully.')
