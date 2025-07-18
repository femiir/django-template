from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from ninja import PatchDict, Router

from common.schema import APIResponse, APIResponseWithData, make_data_response, make_response
from notifications.models import NotificationPreference
from notifications.schema.notifications import BroadcastNotificationInSchema, NotificationPreferenceSchema
from tasks.notifications.broadcast_tasks import send_broadcast_notification_task

notifications_router = Router(tags=['Notifications'])
User = get_user_model()


@notifications_router.get(
	'/notification-settings/',
	response={200: APIResponseWithData[NotificationPreferenceSchema], 404: APIResponse},
)
def get_notification_settings(request) -> dict:
	user = request.user
	if not user.is_authenticated:
		return 404, make_response(False, 404, 'User not found.')

	preference = get_object_or_404(NotificationPreference, user=user)
	return 200, make_data_response(data=preference, message='Notification settings retrieved successfully.')


@notifications_router.patch(
	'/update-notification-settings/',
	response={200: APIResponseWithData[NotificationPreferenceSchema], 400: APIResponse},
)
def update_notification_settings(request, payload: PatchDict[NotificationPreferenceSchema]) -> dict:
	user = request.user

	preference = get_object_or_404(NotificationPreference, user=user)

	if payload.get('sms') is True and not getattr(user, 'phone_number', None):
		return 400, make_response(
			success=False, status_code=404, message='You must add a phone number to enable SMS notifications.'
		)
	for key, value in payload.items():
		if hasattr(preference, key):
			setattr(preference, key, value)
	preference.modify()
	preference.save()
	return 200, make_data_response(message='Notification settings updated successfully.', data=preference)


@notifications_router.post(
	'/create-notification/',
	response={201: APIResponse, 400: APIResponse},
)
def create_notification(request, payload: BroadcastNotificationInSchema) -> dict:
	user = request.user
	if not user.is_authenticated:
		return make_response(False, 400, 'User not authenticated.')

	send_broadcast_notification_task.defer(
		verb=payload.verb,
		message=payload.message,
		target=payload.target,
		source_app='accounts',
		admin_user=user.id,
	)
	return 201, make_response(success=True, status_code=201, message='Notification created successfully.')
