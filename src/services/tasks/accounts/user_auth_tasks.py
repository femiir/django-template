import logging

from django.contrib.auth import get_user_model
from procrastinate.contrib.django import app

from otp.models import OtpType
from services.mail.email import render_template, send_email
from services.otp.otp_managers import create_otp

User = get_user_model()

logger = logging.getLogger('procrastinate')


@app.task(queue='user_signup', retry=2)
def signup_user_task(user, domain_name: str) -> dict:
	"""
	Task to handle user signup and send a verification email.
	"""
	logger.info(f'Starting signup task for user: {user}')
	user = User.objects.get(id=user)

	try:
		_otp = create_otp(user=user, otp_type=OtpType.SIGNUP)
	except Exception as e:
		raise RuntimeError(f'Failed to create OTP: {e!s}')

	# Send signup email
	send_email(
		to_email=user.email,
		html_content=render_template(
			template_name='mails/signup_mail.html',
			context={
				'otp_code': _otp.otp_code,
				'domain_name': domain_name,
			},
		),
		subject='Your Signup Verification Code',
	)
	logger.info(f'Signup email sent to {user.email} with OTP code {_otp.otp_code}')
	return {
		'user_id': user.id,
		'email': user.email,
		'message': 'User created successfully and verification email sent.',
	}


@app.task(queue='otp_request', retry=2)
def request_otp_task(otp_code, user_email) -> dict:
	"""
	Task to handle OTP requests for various purposes.
	"""
	logger.info(f'Starting OTP request task for code: {otp_code} ')
	user = User.objects.filter(email=user_email.lower()).first()
	if not user:
		raise RuntimeError(f'User with email {user_email} does not exist.')
	try:
		# Send OTP via email
		send_email(
			to_email=user.email,
			html_content=render_template(
				template_name='mails/otp_mail.html',
				context={'otp_code': otp_code},
			),
			subject='Your OTP Code',
		)
		logger.info(f'OTP email sent to {user.email} with code {otp_code}')
		return {
		'user_id': user.id,
		'email': user.email,
		'message': 'OTP created successfully and sent via email.',
	}
	except Exception as e:
		logger.error(f'Failed to send OTP email: {str(e)}')
		raise RuntimeError(f'Failed to send OTP email: {str(e)}')
