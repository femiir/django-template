import logging

from django.contrib.auth import get_user_model
from procrastinate.contrib.django import app

from services.mail.email import render_template, send_email

User = get_user_model()

logger = logging.getLogger('procrastinate')


@app.task(queue='mails', retry=2)
def send_email_task(user_email, template_type, category, **kwargs) -> dict:
	"""
	Task to handle OTP requests for various purposes.
	"""
	logger.info(f'Starting email task for: {user_email}')

	try:
		html_content = render_template(
			template_type=template_type, category=category, context=kwargs.get('context')
		)
		send_email(
			to_email=user_email,
			html_content=html_content,
			subject=kwargs.get('subject', 'mail from a trusted source'),
		)
		logger.info(f'Email sent to {user_email} with code {kwargs.get("otp_code")}')
	except Exception as e:
		logger.error(f'Failed to send email: {e!s}')
