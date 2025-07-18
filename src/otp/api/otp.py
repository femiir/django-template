from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.throttling import AnonRateThrottle, UserRateThrottle

from common.schema import APIResponse, make_response
from otp.models import Otp, OtpType
from otp.schema.otp import OtpValidateIn
from services.otp.otp_service import create_otp, verify_otp
from tasks.notifications.mail_tasks import send_email_task
from datetime import datetime

otp_router = Router(tags=['OTP'], auth=None, throttle=AnonRateThrottle('1/m'))
User = get_user_model()


@otp_router.post(
	'/validate/', response={200: APIResponse, 400: APIResponse, 404: APIResponse}
)
def validate_otp(request, payload: OtpValidateIn):
	"""Validate OTP Code."""
	user = get_object_or_404(User, email=payload.email.lower())
	if payload.otp_type not in OtpType.values:
		return make_response(False, 400, 'Invalid OTP type.')
	success, message = verify_otp(
		user=user,
		otp_code=payload.otp_code,
		otp_type=OtpType(payload.otp_type)
	)
	if not success:
		return make_response(False, 400, message)
	if payload.otp_type == OtpType.SIGNUP:
		user.is_active = True
		user.is_verified = True
		user.save()
		message = 'OTP validated successfully. Your account is now active.'
	return make_response(True, 200, message)


@otp_router.post(
	'/resend/',
	response={200: APIResponse, 400: APIResponse, 404: APIResponse},
	url_name='resend_otp'
)
def request_otp(request, email: str, otp_type: str):
	"""Every Mail That Requires OTP Should Use This Endpoint."""
	user = get_object_or_404(User, email=email.lower())

	if otp_type not in OtpType.values:
		return make_response(False, 400, 'Invalid OTP type.')

	Otp.objects.filter(user=user, otp_type=otp_type, is_used=False).update(is_used=True)

	try:
		otp = create_otp(user=user, otp_type=OtpType(otp_type))
	except Exception as e:
		return make_response(False, 400, f'Failed to create OTP: {e!s}')
	send_email_task.defer(
		user_email=otp.user.email,
		template_type=otp_type,
		category='otp',
		context={
			'otp_code': otp.otp_code,
			'current_year': datetime.now().year,
			'user_name': user.full_name,
		},
		subject=f'Your OTP for {otp_type}',
	) 
	return make_response(True, 200, 'OTP resent successfully.')
