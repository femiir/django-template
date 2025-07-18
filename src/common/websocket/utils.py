"""
Simple WebSocket utilities for Django Channels
"""

import json
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketUtils:
	"""Simple utility class for WebSocket operations"""

	@staticmethod
	def generate_session_id() -> str:
		"""Generate unique session ID"""
		return f'ws_{uuid.uuid4().hex[:12]}'

	@staticmethod
	def get_current_timestamp() -> str:
		"""Get current timestamp in ISO format"""
		return datetime.now().isoformat()

	@staticmethod
	async def safe_send_json(consumer, data: dict):
		"""Safely send JSON data through WebSocket"""
		try:
			await consumer.send(text_data=json.dumps(data, default=str))
		except Exception as e:
			logger.error(f'❌ Error sending JSON: {e}')

	@staticmethod
	def parse_message(text_data: str) -> tuple[dict | None, str | None]:
		"""Parse WebSocket message with basic validation"""
		try:
			message = json.loads(text_data)
			if not isinstance(message, dict) or not message.get('type'):
				return None, 'Invalid message format'
			return message, None
		except json.JSONDecodeError:
			return None, 'Invalid JSON'
		except Exception as e:
			return None, f'Parse error: {e}'
