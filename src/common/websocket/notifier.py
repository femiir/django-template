# src/common/websocket/notifier.py

import logging
from typing import Any

from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


class WebSocketNotifier:
	"""Simple utility for WebSocket messaging - used by services and consumers"""

	@staticmethod
	async def send_to_user(
		user_id: int,
		message_data: dict[str, Any],
		group_prefix: str = 'notifications',
		message_type: str = 'notification_message',
	) -> bool:
		"""
		Send a message to a specific online user.
		"""
		try:
			channel_layer = get_channel_layer()
			user_group = f'{group_prefix}_user_{user_id}'

			await channel_layer.group_send(
				user_group,
				{
					'type': message_type,
					'data': message_data,
				},
			)

			logger.debug(f'✅ Message sent to user {user_id} ({group_prefix})')
			return True

		except Exception as e:
			logger.error(f'❌ Error sending to user {user_id}: {e}')
			return False

	@staticmethod
	async def send_to_group(
		group_name: str,
		message_data: dict[str, Any],
		message_type: str = 'group_message',
	) -> bool:
		"""
		Send a message to a group/room.

		Returns:
		    True if sent successfully, False on error
		"""
		try:
			channel_layer = get_channel_layer()

			await channel_layer.group_send(
				group_name,
				{
					'type': message_type,
					'data': message_data,
				},
			)

			logger.debug(f'✅ Message sent to group {group_name}')
			return True

		except Exception as e:
			logger.error(f'❌ Error sending to group {group_name}: {e}')
			return False
		except Exception as e:
			logger.error(f'❌ Error sending to group {group_name}: {e}')
			return False
