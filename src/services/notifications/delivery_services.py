import logging

from common.websocket.notifier import WebSocketNotifier
from tasks.notifications.mail_tasks import send_email_task
from tasks.notifications.sms_tasks import send_sms_task

logger = logging.getLogger(__name__)


class DeliveryHandlers:
	"""
	Base class for handling delivery of notifications.
	"""

	@staticmethod
	def handle_email(channel):
		"""
		Handle email delivery.
		"""
		try:
			notification = channel.notification
			user_email = notification.user.email
			subject = f'Notification: {notification.verb}'
			message = notification.message or 'You have a new notification.'

			send_email_task.defer(
				user_email=user_email,
				template_type=notification.verb,
				category='notification',
				context={
					# Required for template
					'user_name': notification.user.full_name,
					'message': message,
				},
				subject=subject,
			)
			channel.status = 'sent'
			channel.save()
		except Exception as e:
			logger.error('Failed to send email notification: %s', str(e))
			channel.status = 'failed'
			channel.save()
			raise RuntimeError(f'Failed to send email: {e!s}')

	@staticmethod
	def handle_sms(channel):
		"""
		Handle SMS delivery.
		"""
		try:
			notification = channel.notification
			user = notification.user.phone_number
			message = notification.message or 'You have a new notification.'

			if not hasattr(notification.user, 'phone_number') or not notification.user.phone_number:
				channel.status = 'failed'
				channel.save()
				return

			send_sms_task.defer(to_number=user, message=message)
			channel.status = 'sent'
			channel.save()
		except Exception as e:
			logger.error('Failed to send SMS notification: %s', str(e))
			channel.status = 'failed'
			channel.save()
			raise RuntimeError(f'Failed to send SMS: {e!s}')

	@staticmethod
	def handle_push(channel):
		"""
		Handle push notification delivery via WebSocket.
		Only sends if user is online
		"""
		try:
			notification = channel.notification
			user = notification.user
			message = notification.message or 'You have a new notification.'

			notification_data = {
				'id': notification.id,
				'verb': notification.verb,
				'message': message,
				'source_app': notification.source_app,
				'actor': str(notification.actor) if notification.actor else None,
				'target': str(notification.target) if notification.target else None,
				'created_at': notification.created_at.isoformat(),
				'read': notification.read,
				'type': 'new_notification',
				'timestamp': notification.created_at.isoformat(),
			}
			success = WebSocketNotifier.send_to_user(
				user_id=user.id,
				message_data=notification_data,
				message_type='notification_message',
			)
			if success:
				channel.status = 'sent'
				logger.info(f'✅ Push notification sent to online user {user.id} via WebSocket')
			else:
				pass
		except Exception as e:
			logger.error('Failed to send push notification: %s', str(e))
			channel.status = 'failed'
			channel.save()
			raise RuntimeError(f'Failed to send push notification: {e!s}')
