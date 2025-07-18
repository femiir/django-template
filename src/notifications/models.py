from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from common.base_model import TimeStampedSoftDeleteModel

User = settings.AUTH_USER_MODEL


class NotificationChannelType(models.TextChoices):
	EMAIL = 'email', 'Email'
	SMS = 'sms', 'SMS'
	PUSH = 'push', 'Push'


class NotificationVerb(models.TextChoices):
	LIKE = 'like', 'Like'
	COMMENT = 'comment', 'Comment'
	FOLLOW = 'follow', 'Follow'
	MENTION = 'mention', 'Mention'
	SHARE = 'share', 'Share'
	OTHER = 'other', 'Other'
	REPORT = 'report', 'Report'
	ISSUE = 'issue', 'Issue'
	RESOLVED = 'resolved', 'Resolved'
	BROADCAST = 'broadcast', 'Broadcast'

	# TODO will be to add a class for template context based on the verb and tweak the handle email method or go ahead and return a context basesd on the verb

	@classmethod
	def get_template(cls, verb=None):
		"""
		Return the path to the generic notification email template.
		The context passed to the template should include 'message' and any other dynamic fields needed.
		"""
		return 'mails/notifications/notification.html'


class Notification(TimeStampedSoftDeleteModel):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	message = models.TextField(blank=True, null=True)
	read = models.BooleanField(default=False)
	source_app = models.CharField(max_length=100, blank=True, null=True)
	verb = models.CharField(max_length=255, choices=NotificationVerb.choices, default=NotificationVerb.OTHER)

	actor_content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
	actor_object_id = models.PositiveIntegerField(null=True, blank=True)
	actor = GenericForeignKey('actor_content_type', 'actor_object_id')

	target_content_type = models.ForeignKey(
		ContentType, on_delete=models.SET_NULL, null=True, blank=True, related_name='+'
	)
	target_object_id = models.PositiveIntegerField(null=True, blank=True)
	target = GenericForeignKey('target_content_type', 'target_object_id')

	class Meta:
		ordering = ['-created_at']
		verbose_name = 'Notification'
		verbose_name_plural = 'Notifications'
		db_table = 'notifications_table'

	def __str__(self):
		return f'Notification to {self.user}: {self.verb}'


class NotificationChannel(TimeStampedSoftDeleteModel):
	"""
	Defines the delivery channels for notifications.
	"""

	notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='channels')
	channel_type = models.CharField(
		max_length=50, choices=NotificationChannelType.choices, default=NotificationChannelType.EMAIL
	)
	status = models.CharField(
		max_length=50,
		choices=[
			('pending', 'Pending'),
			('sent', 'Sent'),
			('failed', 'Failed'),
		],
		default='pending',
	)

	def __str__(self):
		return f'{self.channel_type} for {self.notification.user.email}'

	class Meta:
		verbose_name = 'Notification Channel'
		verbose_name_plural = 'Notification Channels'
		db_table = 'notification_channels_table'


class NotificationPreference(TimeStampedSoftDeleteModel):
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preferences'
	)
	email = models.BooleanField(default=True)
	sms = models.BooleanField(default=False)
	push = models.BooleanField(default=True)

	def __str__(self):
		return f'Preferences for {self.user.email}'
