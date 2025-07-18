"""
Simple Redis-based online user tracking for WebSocket real-time messaging
Only tracks who's online - no complex session/device management
"""

import logging

from redis import asyncio as aioredis
from django.conf import settings

logger = logging.getLogger(__name__)


class UserState:
	"""Simple online user tracking for WebSocket messaging"""

	def __init__(self):
		self.redis: aioredis.Redis | None = None
		self.redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
		self.ONLINE_USERS_KEY = 'users:online'
		self.TIMEOUT = 300  # 5 minutes

	async def get_redis(self) -> aioredis.Redis:
		"""Get or create Redis connection"""
		if self.redis is None:
			self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
		return self.redis

	async def set_user_online(self, user_id: int) -> bool:
		"""Mark user as online"""
		try:
			redis = await self.get_redis()
			await redis.sadd(self.ONLINE_USERS_KEY, user_id)
			await redis.expire(self.ONLINE_USERS_KEY, self.TIMEOUT)
			logger.debug(f'✅ User {user_id} is online')
			return True
		except Exception as e:
			logger.error(f'❌ Error setting user {user_id} online: {e}')
			return False

	async def set_user_offline(self, user_id: int) -> bool:
		"""Mark user as offline"""
		try:
			redis = await self.get_redis()
			await redis.srem(self.ONLINE_USERS_KEY, user_id)
			logger.debug(f'✅ User {user_id} is offline')
			return True
		except Exception as e:
			logger.error(f'❌ Error setting user {user_id} offline: {e}')
			return False

	async def get_online_users(self) -> set[int]:
		"""Get all online users"""
		try:
			redis = await self.get_redis()
			user_ids = await redis.smembers(self.ONLINE_USERS_KEY)
			return {int(uid) for uid in user_ids if uid.isdigit()}
		except Exception as e:
			logger.error(f'❌ Error getting online users: {e}')
			return set()

	async def is_user_online(self, user_id: int) -> bool:
		"""Check if user is online"""
		try:
			redis = await self.get_redis()
			return await redis.sismember(self.ONLINE_USERS_KEY, user_id)
		except Exception as e:
			logger.error(f'❌ Error checking if user {user_id} is online: {e}')
			return False

	async def close(self):
		"""Close Redis connection"""
		if self.redis:
			await self.redis.close()
			self.redis = None


# Global instance
user_state = UserState()


# Convenience functions for easy import
async def async_set_user_online(user_id: int) -> bool:
	return await user_state.set_user_online(user_id)


async def async_set_user_offline(user_id: int) -> bool:
	return await user_state.set_user_offline(user_id)


async def async_get_all_online_users() -> set[int]:
	return await user_state.get_online_users()


async def async_is_user_online(user_id: int) -> bool:
	return await user_state.is_user_online(user_id)
