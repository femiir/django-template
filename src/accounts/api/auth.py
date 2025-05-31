from ninja import Router
from ninja.errors import HttpError

from accounts.jwt.token import get_access_token_for_user, get_refresh_token_for_user
from accounts.models import User
from accounts.schema.auth import Token, UserIn
from common.schema import APIResponse, APIResponseWithData, make_data_response
from services.tasks.accounts.user_auth_tasks import signup_user_task



auth_router = Router(tags=['Auth'], auth=None)


@auth_router.post(
	'/register/',
	response={200: APIResponseWithData[Token], 400: APIResponse},
	url_name='register',
)
def register(request, payload: UserIn) -> dict:
	try:
		user = User.objects.create_user(**payload.model_dump())
	except Exception as e:
		raise HttpError(message=str(e), status_code=400) from e
	# Send signup email
	domain_name = request.headers.get('x-domain-name', request.get_host())
	signup_user_task.defer(
		user=user.id,
		domain_name=domain_name,
	)

	refresh_token, _ = get_refresh_token_for_user(user)
	access_token, _ = get_access_token_for_user(user)
	return make_data_response(
		status_code=200,
		message='User registered successfully',
		data={'refresh': refresh_token, 'access': access_token},
	)