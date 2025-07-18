from django.urls import re_path

import notifications.consumers.notifications as notifications_consumers

notification_websocket_urlpatterns = [
	re_path(r'ws/notifications/$', notifications_consumers.NotificationConsumer.as_asgi()),
]
