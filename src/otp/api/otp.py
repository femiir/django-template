from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from ninja import Router

from common.schema import APIResponse, make_response
from otp.models import Otp, OtpType
from otp.schema.otp import OtpValidateIn
from services.tasks.accounts.user_auth_tasks import request_otp_task
from services.otp.otp_managers import create_otp
from ninja.throttling import AnonRateThrottle

otp_router = Router(tags=['OTP'])
User = get_user_model()


@otp_router.post(
	'/validate/', response={200: APIResponse, 400: APIResponse, 404: APIResponse}
)
def validate_otp(request, payload: OtpValidateIn):
	try:
		otp = Otp.objects.select_related('user').get(
			user__email=payload.email,
			otp_code=payload.otp_code,
			otp_type=payload.otp_type,
			is_used=False,
		)
	except Otp.DoesNotExist:
		return make_response(False, 400, 'Invalid or already used OTP.')

	if otp.is_expired():
		return make_response(False, 400, 'OTP has expired.')

	otp.mark_as_used()
	if payload.otp_type == 'signup':
		user = otp.user
		user.is_active = True
		user.is_verified = True
		user.save()
	elif payload.otp_type == 'password_reset':
		user = otp.user
		user.set_password(payload.new_password)
		user.save()
	return make_response(True, 200, 'OTP validated successfully.')


@otp_router.post(
	'/resend/',
	response={200: APIResponse, 400: APIResponse, 404: APIResponse},
	url_name='resend_otp', throttle=AnonRateThrottle('2/m')
)
def resend_otp(request, email: str, otp_type: str):
	user = get_object_or_404(User, email=email.lower())
	# Validate otp_type
	if otp_type not in OtpType.values:
		return make_response(False, 400, 'Invalid OTP type.')

	# Invalidate previous OTPs of this type
	Otp.objects.filter(user=user, otp_type=otp_type, is_used=False).update(is_used=True)
	# Create a new OTP
	try:
		otp = create_otp(user=user, otp_type=OtpType(otp_type))
	except Exception as e:
		return make_response(False, 400, f'Failed to create OTP: {str(e)}')
	request_otp_task.defer(otp_code=otp.otp_code, user_email=otp.user.email)
	return make_response(True, 200, 'OTP resent successfully.')
