from unicodedata import category
import resend
from django.conf import settings
from django.template.loader import get_template

from notifications.models import NotificationVerb
from otp.models import OtpType

RESEND_API_KEY = getattr(settings, 'RESEND_API_KEY', None)
REPLY_TO = getattr(settings, 'REPLY_TO', None)
FROM_EMAIL = getattr(settings, 'FROM_EMAIL', 'no-reply@example.com')

resend.api_key = RESEND_API_KEY


TEMPLATE_RESOLVERS = {
	'otp': OtpType,
	'notification': NotificationVerb,
	# add more as needed
}


def get_email_template(template_type: str, category, default: str = None) -> str:

	template_class = TEMPLATE_RESOLVERS.get(category)
	if not template_class or not hasattr(template_class, 'get_template'):
		if default:
			return default
		raise ValueError(f"Unknown or invalid template class for category '{category}'")

	return template_class.get_template(template_type)


def render_template(template_type: str, category: str, context: dict) -> str:
	"""
	Render a template with the given context, based on template type and category.
	"""
	template_name = get_email_template(template_type, category)
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
