"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import logging
import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

# Set up logging to see rejection reasons
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')


from middlewares.jwt.JWTAuthMiddlewareChannels import JWTAuthMiddlewareStack
from notifications.routers.notifications import notification_websocket_urlpatterns

_app = get_asgi_application()

application = ProtocolTypeRouter({
	'http': _app,
	'websocket': JWTAuthMiddlewareStack(
		URLRouter(notification_websocket_urlpatterns)
	),
})
