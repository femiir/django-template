from enum import Enum

from ninja import Field, FilterSchema, ModelSchema, Schema

from accounts.models import UserType

from ..models import Notification, NotificationPreference

_exclude = ['id', 'user', 'created_at', 'modified', 'deleted_at', 'is_deleted']


class NotificationPreferenceSchema(ModelSchema):
	"""
	Schema for validating OTP.
	"""

	class Meta:
		model = NotificationPreference
		fields = ['email', 'sms', 'push']



class NotificationFilterSchema(FilterSchema):
	"""
	Schema for filtering notifications.
	"""

	user: str | None = Field(None, q='user__email')
	verb: str | None = Field(None, q='verb')
	read: bool | None = Field(None, q='read')
	source_app: str | None = Field(None, q='source_app')

	class Config:
		expression_connector = 'OR'


class NotificationOutSchema(ModelSchema):
	"""
	Schema for serializing notifications.
	"""

	class Meta:
		model = Notification
		fields = [
			'id',
			'verb',
			'message',
			'read',
		]



class BroadcastNotificationInSchema(Schema):
	"""
	Schema for creating a new notification.
	"""

	target: str = 'all_users'
	verb: str
	message: str | None = None
	