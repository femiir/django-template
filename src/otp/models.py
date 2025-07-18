from datetime import timedelta

from django.db import models
from django.utils import timezone

from common.base_model import TimeStampedSoftDeleteModel

# Create your models here.


class OtpType(models.TextChoices):
	SIGNUP = 'signup', 'Signup'
	PASSWORD_RESET = 'password_reset', 'Password Reset'
	RESEND = 'resend', 'Resend OTP'
	ACCOUNT_DELETE = 'account_delete', 'Account Delete'
	ACCOUNT_RESTORE = 'account_restore', 'Account Restore'
	ACCOUNT_DELETION_CONFIRMATION = (
		'account_deletion_confirmation',
		'Account Deletion Confirmation',
	)

	@classmethod
	def get_template(cls, otp_type: str) -> str:
		"""
		Get the email template associated with the given OTP type.
		"""
		template_mapping = {
			cls.SIGNUP: 'mails/otp/signup_mail.html',
			cls.PASSWORD_RESET: 'mails/otp/password_reset.html',
			cls.RESEND: 'mails/otp/otp_mail.html',
			cls.ACCOUNT_DELETE: 'mails/otp/account_delete_mail.html',
			cls.ACCOUNT_RESTORE: 'mails/otp/account_restore_mail.html',
			cls.ACCOUNT_DELETION_CONFIRMATION: 'mails/otp/account_deletion_confirmation_mail.html',
		}
		
		return template_mapping.get(otp_type)


class Otp(TimeStampedSoftDeleteModel):
	user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
	otp_code = models.CharField(max_length=6)
	otp_type = models.CharField(
		max_length=50, choices=OtpType.choices, default=OtpType.SIGNUP
	)
	is_used = models.BooleanField(default=False)
	expires_at = models.DateTimeField()

	def __str__(self):
		return f'{self.user.email} - {self.otp_type} - {self.otp_code}'

	class Meta:
		verbose_name = 'OTP'
		verbose_name_plural = 'OTPs'
		ordering = ['-created_at']
		db_table = 'otp_codes'

	@staticmethod
	def get_expiration_time(duration=10):
		"""
		Returns the expiration time for the OTP.
		The default duration is 10 minutes.
		"""
		if not isinstance(duration, int) or duration <= 0:
			raise ValueError(
				'Duration must be a positive integer representing minutes.'
			)
		if duration > 60:
			raise ValueError('Duration cannot exceed 60 minutes.')
		return timezone.now() + timedelta(minutes=duration)

	def is_expired(self):
		return timezone.now() > self.expires_at

	def mark_as_used(self):
		self.is_used = True
		self.save(update_fields=['is_used'])

	def save(self, *args, **kwargs):
		if not self.expires_at:
			self.expires_at = self.get_expiration_time()
		super().save(*args, **kwargs)
