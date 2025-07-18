# accounts/manager.py

from urllib.parse import urlencode, unquote

from django.conf import settings
from django.contrib.auth.models import BaseUserManager
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.db import models
from django.utils.timezone import now


class UserTypeManager(models.Manager):
	def __init__(self, user_type=None, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.user_type = user_type

	def get_queryset(self):
		qs = super().get_queryset()
		if self.user_type:
			return qs.filter(user_type=self.user_type)
		return qs


class CustomUserManager(BaseUserManager):
	def create_user(self, email, password=None, **extra_fields):
		if not email:
			raise ValueError('The Email is required')
		email = self.normalize_email(email)
		user = self.model(email=email, **extra_fields)
		user.set_password(password)
		user.is_active = True
		user.save(using=self._db)
		return user

	def create_staffuser(self, email, password=None, **extra_fields):
		extra_fields.setdefault('is_staff', True)
		extra_fields.setdefault('is_superuser', False)
		return self.create_user(email, password, **extra_fields)

	def create_superuser(self, email, password=None, **extra_fields):
		extra_fields.setdefault('is_active', True)
		extra_fields.setdefault('is_staff', True)
		extra_fields.setdefault('is_superuser', True)
		return self.create_user(email, password, **extra_fields)


def signing_dumps(request, purpose: str, payload=None):
	signer = TimestampSigner()
	data = {
		**(payload or {}),
		'purpose': purpose,
		'timestamp': now().isoformat(),
		'ip': request.META.get('REMOTE_ADDR'),
		'ua': request.META.get('HTTP_USER_AGENT', ''),
	}
	token = signer.sign_object(data)
	query = urlencode({'token': token})
	return f'{settings.FRONTEND_URL}/?{query}'


def verify_signed_data(token: str, max_age: int = 3600) -> dict:
	"""
	Verify and deserialize the signed token, checking for expiration.
	:param token: The signed token to verify.
	:param max_age: The maximum age of the token in seconds.
	:return: The deserialized payload if valid.
	:raises ValueError: If the token is invalid or expired.
	"""
	signer = TimestampSigner()
	try:
		# Unsign the token and enforce expiration
		decoded_token = unquote(token)
		data = signer.unsign_object(decoded_token, max_age=max_age)
		return data
	except SignatureExpired:
		raise ValueError('The token has expired.')
	except BadSignature:
		raise ValueError('Invalid token.')
