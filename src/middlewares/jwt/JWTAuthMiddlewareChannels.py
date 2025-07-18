import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware

logger = logging.getLogger(__name__)


class JWTAuthMiddleware(BaseMiddleware):
	async def __call__(self, scope, receive, send):
		# Import here to avoid Django startup issues
		from middlewares.jwt.token import get_user_from_token

		query_string = scope.get('query_string', b'').decode()
		token = parse_qs(query_string).get('token', [None])[0]
		user = None

		if token:
			try:
				user = await database_sync_to_async(get_user_from_token)(token)
			except Exception as e:
				logger.error(f'JWT Middleware: Error getting user from token: {e}')
		else:
			logger.warning('JWT Middleware: No token provided, user will be None')
		scope['user'] = user

		# Only allow authenticated users - reject if no valid user
		if user is None:
			logger.warning('JWT Middleware: WebSocket connection rejected - no authenticated user')
			# Close the connection by sending a close frame
			await send({
				'type': 'websocket.close',
				'code': 4001,  # Custom close code for authentication failure
				'reason': 'Authentication required',
			})
			return

		return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
	from channels.auth import AuthMiddlewareStack

	return JWTAuthMiddleware(AuthMiddlewareStack(inner))
