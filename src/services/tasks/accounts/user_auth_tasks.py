import logging

from procrastinate.contrib.django import app

from otp.models import Otp, OtpType
from services.mail.email import render_template, send_email
from services.mail.generate_otp import generate_otp_code
from django.contrib.auth import get_user_model

User = get_user_model()

logger = logging.getLogger('procrastinate')


@app.task(queue='user_signup', retry=2)
def signup_user_task(user, domain_name: str) -> dict:
	"""
	Task to handle user signup and send a verification email.
	"""
	logger.info(f'Starting signup task for user: {user}')
	user = User.objects.get(id=user)

	otp_code = generate_otp_code()

	try:
		_otp = Otp.objects.create(
			user=user,
			otp_code=otp_code,
			otp_type=OtpType.SIGNUP,
			# uncomment the next line if you want to set a specific expiration time
			# expires_at=Otp.get_expiration_time(1)
		)
	except Exception as e:
		raise RuntimeError(f'Failed to create OTP: {e!s}')

	# Send signup email
	send_email(
		to_email=user.email,
		html_content=render_template(
			template_name='mails/signup_mail.html',
			context={
				'otp_code': otp_code,
				'domain_name': domain_name,
			},
		),
		subject='Your Signup Verification Code',
	)
	logger.info(f'Signup email sent to {user.email} with OTP code {otp_code}')
	return {
		'user_id': user.id,
		'email': user.email,
		'message': 'User created successfully and verification email sent.',
	}
