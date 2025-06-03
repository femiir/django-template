from django.shortcuts import get_object_or_404
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from ninja import PatchDict, Query, Router
from ninja.errors import AuthenticationError, AuthorizationError, HttpError

from accounts.models import User, UserType
from accounts.schema.auth import (
	Login,
	Token,
	TokenRefreshRequest,
	UserFilter,
	UserIn,
	UserOut,
	UserUpdate,
)
from common.account_manager import get_user_profile_instance
from common.schema import APIResponse, APIResponseWithData, make_data_response, make_response
from services.tasks.accounts.user_auth_tasks import signup_user_task
from tokens.jwt.token import (
	TokenTypes,
	blacklist_token,
	decode_token,
	get_access_token_from_refresh_token,
	get_obtain_token_pair,
)

auth_router = Router(tags=['Auth'])


@auth_router.post(
	'/register/',
	response={200: APIResponseWithData[Token], 400: APIResponse},
	url_name='register',
	auth=None,
)
def register(request, payload: UserIn) -> dict:
	try:
		user = User.objects.create_user(**payload.model_dump())
	except Exception as e:
		raise AuthenticationError(message=str(e), status_code=400) from e
	# Send signup email
	domain_name = request.headers.get('x-domain-name', request.get_host())
	signup_user_task.defer(
		user=user.id,
		domain_name=domain_name,
	)

	token = get_obtain_token_pair(user)
	return make_data_response(
		status_code=200,
		message='User registered successfully',
		data={'refresh': token['refresh_token'], 'access': token['access_token']},
	)


@auth_router.post(
	'/login/',
	response={200: APIResponseWithData[Token], 400: APIResponse},
	url_name='login',
	auth=None,
)
def login(request, payload: Login) -> dict:
	try:
		user = get_object_or_404(User, email=payload.email)
		if not user.check_password(payload.password):
			raise AuthenticationError(message='Invalid credentials', status_code=400)
		if not user.is_active or not user.is_verified:
			raise AuthorizationError(
				message='User is not active or verified', status_code=400
			)
		token = get_obtain_token_pair(user)
		return make_data_response(
			status_code=200,
			message='User logged in successfully',
			data={'refresh': token['refresh_token'], 'access': token['access_token']},
		)
	except User.DoesNotExist:
		raise HttpError(message='User does not exist', status_code=400) from None
	except Exception as e:
		raise HttpError(message=str(e), status_code=400) from e

@auth_router.get(
	'/current_user/', response={200: APIResponseWithData[UserOut], 400: APIResponse}
)
def current_user(request) -> dict:
	user = request.user
	if not user.is_authenticated:
		raise HttpError(message='User is not authenticated', status_code=400)

	profile = get_user_profile_instance(user)
	if not profile:
		raise HttpError(message='User profile does not exist', status_code=400)
	user_out = UserOut.from_orm(user)
	user_out.profile = profile

	return make_data_response(
		status_code=200,
		message='Current user retrieved successfully',
		data=user_out,
	)


@auth_router.patch(
	'/update_profile/',
	response={200: APIResponseWithData[UserOut], 400: APIResponse},
	url_name='update_profile',
)
def update_profile(request, payload: PatchDict[UserUpdate]) -> dict:
	user = request.user
	if not user.is_authenticated:
		raise HttpError(message='User is not authenticated', status_code=400)

	profile_instance = get_user_profile_instance(user)
	if not profile_instance:
		raise HttpError(message='User profile does not exist', status_code=400)

	user_data = payload
	if 'profile' in user_data:
		profile_data = user_data.pop('profile', {})
		for key, value in profile_data.items():
			setattr(profile_instance, key, value)
		profile_instance.save()
	for key, value in user_data.items():
		setattr(user, key, value)
	user.save()
	user_out = UserOut.from_orm(user)
	user_out.profile = get_user_profile_instance(user)

	return make_data_response(
		status_code=200,
		message='User profile updated successfully',
		data=user_out,
	)


@auth_router.get(
	'/user/{user_id}/',
	response={200: APIResponseWithData[UserOut], 400: APIResponse},
	url_name='user_profile',
	auth=None,
)
def request_user_profile(request, user_id: int) -> dict:
	user = get_object_or_404(User, id=user_id)
	profile = get_user_profile_instance(user)
	if not profile:
		raise HttpError(message='User profile does not exist', status_code=400)

	user_out = UserOut.from_orm(user)
	user_out.profile = profile

	return make_data_response(
		status_code=200,
		message='User profile retrieved successfully',
		data=user_out,
	)


@auth_router.get(
	'/all_users/', response={200: APIResponseWithData[list[UserOut]], 400: APIResponse}
)
def all_users(
	request,
	filters: UserFilter = Query(...),
) -> dict:
	if not request.user.is_authenticated:
		raise AuthorizationError(message='User is not authenticated', status_code=400)

	if request.user.user_type != UserType.ADMIN and (
		filters.is_active is False or filters.is_verified is False
	):
		raise AuthorizationError(
			message='Only admin can view inactive or unverified users', status_code=403
		)
	users = User.objects.all().filter(is_superuser=False).exclude(id=request.user.id)
	if (
		request.user.user_type == UserType.VENDOR
		or request.user.user_type == UserType.CUSTOMER
	):
		filters.is_active = True
		filters.is_verified = True
		users = filters.filter(users)
		users = users.filter(user_type__in=[UserType.VENDOR, UserType.CUSTOMER])
	elif request.user.user_type == UserType.ADMIN:
		users = filters.filter(users)
	else:
		raise AuthorizationError(
			message='Only admin, vendor or customer can view all users', status_code=403
		)

	user_out_list = []
	for user in users:
		user_out = UserOut.from_orm(user)
		user_out.profile = get_user_profile_instance(user)
		user_out_list.append(user_out)

	return make_data_response(
		status_code=200,
		message='Users retrieved successfully',
		data=user_out_list,
	)


@auth_router.post(
	'/refresh_token/',
	response={200: APIResponseWithData[Token], 400: APIResponse},
	url_name='refresh_token',
	auth=None,
)
def refresh_token(request, payload: TokenRefreshRequest) -> dict:
	try:
		# Extract the refresh token from the payload
		refresh_token = payload.refresh
		if not refresh_token:
			raise ValueError('Refresh token is required')

		# Generate a new access token using the refresh token
		access_token, _ = get_access_token_from_refresh_token(refresh_token)

		return make_data_response(
			status_code=200,
			message='Token refreshed successfully',
			data={'access': access_token, 'refresh': refresh_token},
		)
	except ExpiredSignatureError:
		raise HttpError(message='Refresh token has expired', status_code=401)
	except InvalidTokenError:
		raise HttpError(message='Invalid refresh token', status_code=401)
	except Exception as e:
		raise HttpError(message=f'Failed to refresh token: {e!s}', status_code=400)


@auth_router.post(
	'/logout/',
	response={200: APIResponse, 400: APIResponse},
	url_name='logout',
	auth=None,  # Allow unauthenticated requests to handle token-based logout
)
def logout(request, payload: TokenRefreshRequest) -> dict:
	try:
		refresh_token = payload.refresh
		if not refresh_token:
			raise ValueError('Refresh token is required')

		decoded = decode_token(
			refresh_token, token_type=TokenTypes.REFRESH, verify=True
		)
		user_id = decoded.get('user_id')
		jti = decoded.get('jti')

		if not user_id or not jti:
			raise ValueError('Invalid refresh token')

		user = get_object_or_404(User, id=user_id)
		blacklist_token(user, refresh_token)

		return make_response(
			success=True,
			message='User logged out successfully',
			status_code=200,
		)
	except ExpiredSignatureError:
		raise HttpError(message='Refresh token has already expired', status_code=401)
	except InvalidTokenError:
		raise HttpError(message='Invalid refresh token', status_code=401)
	except Exception as e:
		raise HttpError(message=f'Failed to logout: {str(e)}', status_code=400)
