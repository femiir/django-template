import hashlib
from datetime import timezone

from django.conf import settings
from django.db import models

from common.base_model import TimeStampedSoftDeleteModel

# Create your models here.


class TrackedToken(TimeStampedSoftDeleteModel):
	"""
	A model that tracks changes to its fields.
	"""

	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='tracked_models',
	)
	jti = models.CharField(max_length=255, unique=True)
	exp = models.DateTimeField()
	access_token = models.TextField(blank=True, null=True, default=None)
	refresh_token = models.TextField(blank=True, null=True, default=None)

	def __str__(self):
		return f'Token {self.jti} for user {self.user.email}'

	def is_expired(self):
		"""
		Check if the token is expired.
		"""
		return self.exp < timezone.now()

	@staticmethod
	def hasher(value):
		"""
		Hash the JTI to ensure it is stored securely.
		"""
		if isinstance(value, str):
			value = value.encode('utf-8')
		return hashlib.sha256(value).hexdigest()

	class Meta:
		verbose_name = 'Tracked Token'
		verbose_name_plural = 'Tracked Tokens'
		ordering = ['-created_at']
		db_table = 'tracked_tokens'


class BlacklistedToken(TimeStampedSoftDeleteModel):
	"""
	A model that tracks blacklisted tokens.
	"""

	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='blacklisted_tokens',
	)
	blacklisted_at = models.DateTimeField(auto_now_add=True)
	token = models.OneToOneField(
		TrackedToken, on_delete=models.CASCADE, related_name='blacklisted_token'
	)

	def __str__(self):
		return f'Blacklisted Token {self.token.jti} for user {self.user.email}'

	class Meta:
		verbose_name = 'Blacklisted Token'
		verbose_name_plural = 'Blacklisted Tokens'
		ordering = ['-created_at']
		db_table = 'blacklisted_tokens'
