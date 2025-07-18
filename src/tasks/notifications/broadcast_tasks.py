# src/tasks/notifications/broadcast_tasks.py
import logging
from datetime import datetime

from django.contrib.auth import get_user_model
from django.db import transaction
from procrastinate.contrib.django import app

from services.notifications.helpers import notify_user

logger = logging.getLogger(__name__)
User = get_user_model()


@app.task(queue='broadcast', retry=2)
def send_broadcast_notification_task(
	verb: str,
	message: str,
	target: str = 'all_users',
	admin_user: int = None,
	chunk_size: int = 100,
	source_app: str = 'accounts',
):
	"""
	Broadcast notifications to users in chunks, dynamically by user type.
	"""
	try:
		# Select users based on target type
		if target == 'all_users':
			# All active, verified users except staff/superusers
			users_queryset = User.objects.filter(is_active=True, is_verified=True).exclude(
				is_staff=True, is_superuser=True
			)
		else:
			# Any other user type (e.g., 'vendor', 'customer', etc.)
			users_queryset = User.objects.filter(is_active=True, is_verified=True, user_type=target)

		# Get user IDs for chunking
		user_ids = list(users_queryset.values_list('id', flat=True))
		total_users = len(user_ids)
		if total_users == 0:
			logger.warning('No active users found for the specified criteria')
			return

		logger.info(f'Starting broadcast to {total_users} users in chunks of {chunk_size}')

		# Calculate number of chunks
		total_chunks = (total_users + chunk_size - 1) // chunk_size

		admin_user = User.objects.get(id=admin_user) if admin_user else None
		# Process each chunk
		for chunk_number in range(total_chunks):
			start = chunk_number * chunk_size
			end = start + chunk_size
			chunk_user_ids = user_ids[start:end]

			# Transaction ensures atomicity for each chunk
			with transaction.atomic():
				for user_id in chunk_user_ids:
					try:
						user = User.objects.get(id=user_id)
						notify_user(
							user=user,
							verb=verb,
							message=message,
							source_app=source_app,
							actor=admin_user,
							target_object=user,
						)
					except Exception as e:
						logger.error(f'Failed to notify user {user_id}: {e!s}')

		logger.info(
			f'Queued {total_chunks} chunks for broadcast processing'
		)  
	except Exception as e:
		logger.error(f'Error in send_broadcast_notification_task: {e!s}')
