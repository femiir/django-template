"""
Simple WebSocket consumer for real-time notifications
Handles connection/disconnection and basic message routing
"""

import logging

from channels.generic.websocket import AsyncWebsocketConsumer

from common.state import async_set_user_offline, async_set_user_online
from common.websocket.utils import WebSocketUtils

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
	"""Simple WebSocket consumer for notifications"""

	async def connect(self):
		"""Handle WebSocket connection"""
		try:
			self.user = self.scope.get('user')
			if not self.user.is_authenticated:
				logger.warning('Unauthenticated connection attempt')
				await self.close()
				return

			self.user_id = self.user.id
			self.session_id = WebSocketUtils.generate_session_id()
			self.user_group = f'notifications_user_{self.user_id}'

			await self.accept()

			await self.channel_layer.group_add(self.user_group, self.channel_name)
			await async_set_user_online(self.user_id)

			# Send connection confirmation
			await WebSocketUtils.safe_send_json(
				self,
				{
					'type': 'connection_established',
					'data': {
						'user_id': self.user_id,
						'session_id': self.session_id,
						'timestamp': WebSocketUtils.get_current_timestamp(),
						'message': 'Connected to notifications',
					},
				},
			)

			logger.info(f'✅ User {self.user_id} connected (session: {self.session_id})')

		except Exception as e:
			logger.error(f'❌ Error during connection: {e}')
			await self.close()

	async def disconnect(self, close_code):
		"""Handle WebSocket disconnection"""
		try:
			if hasattr(self, 'user_id'):
				# Leave user group
				await self.channel_layer.group_discard(self.user_group, self.channel_name)

				# Mark user as offline
				await async_set_user_offline(self.user_id)

				logger.info(f'✅ User {self.user_id} disconnected (code: {close_code})')

		except Exception as e:
			logger.error(f'❌ Error during disconnection: {e}')

	async def receive(self, text_data):
		"""Handle incoming WebSocket messages"""
		try:
			# Parse message
			message, error = WebSocketUtils.parse_message(text_data)
			if error:
				await WebSocketUtils.safe_send_json(
					self,
					{
						'type': 'error',
						'data': {'message': error, 'timestamp': WebSocketUtils.get_current_timestamp()},
					},
				)
				return

			message_type = message.get('type')
			logger.debug(f'Received message type: {message_type} from user {self.user_id}')

			# Route message to appropriate handler
			if message_type == 'ping':
				await self.handle_ping(message)
			elif message_type == 'notification':
				await self.notification_message(message)
			else:
				await WebSocketUtils.safe_send_json(
					self,
					{
						'type': 'error',
						'data': {
							'message': f'Unknown message type: {message_type}',
							'timestamp': WebSocketUtils.get_current_timestamp(),
						},
					},
				)

		except Exception as e:
			logger.error(f'❌ Error handling message from user {self.user_id}: {e}')
			await WebSocketUtils.safe_send_json(
				self,
				{
					'type': 'error',
					'data': {
						'message': 'Internal server error',
						'timestamp': WebSocketUtils.get_current_timestamp(),
					},
				},
			)

	# ========================================
	# MESSAGE HANDLERS
	# ========================================

	async def handle_ping(self, message):
		"""Handle ping for connection keepalive"""
		await WebSocketUtils.safe_send_json(
			self,
			{
				'type': 'pong',
				'data': {
					'timestamp': WebSocketUtils.get_current_timestamp(),
					'session_id': self.session_id,
				},
			},
		)

	async def notification_message(self, event):
		"""Receive and forward notification messages from channel layer"""
		try:
			await WebSocketUtils.safe_send_json(
				self,
				{
					'type': 'notification',
					'data': event['data'],
				},
			)
			logger.debug(f'✅ Notification forwarded to user {self.user_id}')

		except Exception as e:
			logger.error(f'❌ Error forwarding notification to user {self.user_id}: {e}')
