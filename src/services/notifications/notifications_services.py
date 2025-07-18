from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from notifications.models import (
	Notification,
	NotificationChannel,
	NotificationChannelType,
	NotificationPreference,
)

from .delivery_services import DeliveryHandlers

# from tasks.notifications.sms_tasks import send_sms_task
# from tasks.notifications.push_tasks import send_push_task


class NotificationService:
	"""
	Service for managing notifications across multiple channels.
	"""

	@staticmethod
	def create_notification(
		user,  # User model instance
		verb: str,
		message: str = '',
		actor: Any | None = None,
		target_object: Any | None = None,
		source_app: str = '',
	) -> Notification:
		"""
		Create a new notification.
		"""
		with transaction.atomic():
			data = {
				'user': user,
				'verb': verb,
				'message': message,
				'source_app': source_app,
			}

			if actor:
				data['actor_content_type'] = ContentType.objects.get_for_model(actor)
				data['actor_object_id'] = actor.id
			if target_object:
				data['target_content_type'] = ContentType.objects.get_for_model(target_object)
				data['target_object_id'] = target_object.id

			notification = Notification.objects.create(**data)

			delivery_channels: list[NotificationChannelType] = NotificationService._get_user_preferred_channels(
				user
			)
			NotificationService.create_notification_channel(notification, delivery_channels)
			NotificationService.dispatch_notification(notification)

			return notification

	@staticmethod
	def _get_user_preferred_channels(user) -> list[NotificationChannelType]:
		"""
		Get the user's preferred notification channels.
		Always includes 'push' for real-time WebSocket notifications.
		"""
		try:
			_preferences = user.notification_preferences
			preferences = [
				channel for channel in NotificationChannelType if getattr(_preferences, channel.value, False)
			]

			return preferences
		except NotificationPreference.DoesNotExist:
			return [NotificationChannelType.EMAIL, NotificationChannelType.PUSH]

	@staticmethod
	def create_notification_channel(
		notification: Notification,
		channels: list[str],
	) -> None:
		NotificationChannel.objects.bulk_create([
			NotificationChannel(notification=notification, channel_type=channel) for channel in channels
		])

	@staticmethod
	def dispatch_notification(
		notification: Notification,
	) -> None:
		"""
		Dispatch the notification to all channels.
		"""
		for channel in notification.channels.filter(status='pending'):
			handler = getattr(DeliveryHandlers, f'handle_{channel.channel_type.lower()}', None)
			if handler:
				handler(channel)
			else:
				channel.status = 'failed'
				channel.save()
				raise ValueError(f'No handler found for channel type: {channel.channel_type}')

	@staticmethod
	def mark_notification_as_read(
		notification: Notification,
	) -> None:
		"""
		Mark a notification as read.
		"""
		if not notification.read:
			notification.read = True
			notification.save()

			notification.channels.update(is_read=True)

	@staticmethod
	def mark_all_notifications_as_read(
		user,
	) -> None:
		"""
		Mark all notifications for a user as read.
		"""
		notifications = Notification.objects.filter(user=user, read=False)
		for notification in notifications:
			notification.read = True
			notification.save()
			notification.channels.update(is_read=True)

	@staticmethod
	def get_unread_count(user) -> int:
		return Notification.objects.filter(user=user, read=False).count()

	@staticmethod
	def get_user_notifications(user, read: bool | None = None) -> list[Notification]:
		queryset = Notification.objects.filter(user=user)
		if read is not None:
			queryset = queryset.filter(read=read)
		return list(queryset.order_by('-created_at'))

	@staticmethod
	def retry_failed_channels(notification_id: int) -> None:
		notification = Notification.objects.get(id=notification_id)
		failed_channels = notification.channels.filter(status='failed')

		for channel in failed_channels:
			channel.status = 'pending'
			channel.save()

		NotificationService._dispatch_channels(notification)
