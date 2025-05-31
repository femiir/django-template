import resend
from django.conf import settings
from django.template.loader import get_template



RESEND_API_KEY = getattr(settings, 'RESEND_API_KEY', None)
REPLY_TO = getattr(settings, 'REPLY_TO', None)
FROM_EMAIL = getattr(settings, 'FROM_EMAIL', 'no-reply@example.com')

resend.api_key = RESEND_API_KEY


def render_template(template_name: str, context: dict) -> str:
	"""
	Render a template with the given context.
	"""
	template = get_template(template_name)
	return template.render(context)


def send_email(
	to_email: str,
	subject: str = 'Click reply to, to respond to this email',
	html_content: str = None,
	from_email: str = FROM_EMAIL,
	reply_to: str = REPLY_TO,
) -> dict:
	"""
	Send a signup email with OTP code using the Resend API.
	"""


	
	response = resend.Emails.send({
		'from': from_email,
		'to': [to_email],
		'subject': subject,
		'html': html_content,
		'reply_to': reply_to,
	})
	return response
