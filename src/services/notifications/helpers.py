from services.notifications.notifications_services import NotificationService


def notify_user(user, verb, message, actor, target_object, source_app):
	return NotificationService.create_notification(
		user=user,
		verb=verb,
		message=message, 
		actor=actor,
		target_object=target_object,
		source_app=source_app,
	)


def mark_notification_as_read(notification):
	NotificationService.mark_notification_as_read(notification)


def mark_all_notifications_as_read(user):
	NotificationService.mark_all_notifications_as_read(user)


def get_user_notifications(user, limit=20, read=None):
	return NotificationService.get_user_notifications(user, limit, read)


def retry_failed_channels(notification_id):
	NotificationService.retry_failed_channels(notification_id)


def get_unread_count(user):
	return NotificationService.get_unread_count(user)
