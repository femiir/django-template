import os
from datetime import datetime

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from ninja import PatchDict, Query, Router
from ninja.errors import AuthenticationError, AuthorizationError, HttpError

from accounts.models import UserType
from accounts.schema.auth import (
	AccountDeleteVerify,
	Login,
	PasswordResetRequest,
	PasswordResetVerify,
	Token,
	TokenRefreshRequest,
	UserFilter,
	UserIn,
	UserOut,
	UserUpdate,
)
from common.account_manager import signing_dumps, verify_signed_data
from common.schema import APIResponse, APIResponseWithData, make_data_response, make_response
from middlewares.jwt.token import (
	TokenTypes,
	blacklist_all_tokens,
	blacklist_token,
	decode_token,
	get_access_token_from_refresh_token,
	get_obtain_token_pair,
)
from otp.models import OtpType
from services.accounts.accounts_service import (
	delete_user_and_profile,
	get_user_profile_instance,
	restore_user_and_profile,
)
from services.otp.otp_service import create_otp, verify_otp
from tasks.notifications.mail_tasks import send_email_task

auth_router = Router(tags=['Auth'])
User = get_user_model()

domain_name = os.environ.get('PRODUCT_NAME')


@auth_router.post(
	'/register/',
	response={200: APIResponseWithData[Token], 400: APIResponse},
	url_name='register',
	auth=None,
)
def register(request, payload: UserIn) -> dict:
	try:
		user = User.objects.create_user(**payload.model_dump())
	except Exception:
		raise AuthenticationError(message='User Already Exists', status_code=403)
	# Send signup email
	# domain_name = request.headers.get('x-domain-name', request.get_host())
	otp = create_otp(user=user, otp_type=OtpType.SIGNUP)
	if not otp:
		user.delete()
		raise AuthenticationError(message='Failed to create user', status_code=400)

	send_email_task.defer(
		user_email=otp.user.email,
		template_type=OtpType.SIGNUP.value,
		category='otp',
		subject='Welcome to this Space 🚀',
		context={
			'otp_code': otp.otp_code,
			'app_name': domain_name,
			'current_year': datetime.now().year,
			'user_name': user.full_name,
		},
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
			raise AuthorizationError(message='User is not active or verified', status_code=400)
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


@auth_router.get('/current_user/', response={200: APIResponseWithData[UserOut], 400: APIResponse})
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
	'/update-profile/',
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


@auth_router.get('/all-users/', response={200: APIResponseWithData[list[UserOut]], 400: APIResponse})
def all_users(
	request,
	filters: UserFilter = Query(...),
) -> dict:
	if not request.user.is_authenticated:
		raise AuthorizationError(message='User is not authenticated', status_code=400)

	if request.user.user_type != UserType.ADMIN and (
		filters.is_active is False or filters.is_verified is False
	):
		raise AuthorizationError(message='Only admin can view inactive or unverified users', status_code=403)
	users = User.objects.all().filter(is_superuser=False).exclude(id=request.user.id)
	if request.user.user_type == UserType.VENDOR or request.user.user_type == UserType.CUSTOMER:
		filters.is_active = True
		filters.is_verified = True
		users = filters.filter(users)
		users = users.filter(user_type__in=[UserType.VENDOR, UserType.CUSTOMER])
	elif request.user.user_type == UserType.ADMIN:
		users = filters.filter(users)
	else:
		raise AuthorizationError(message='Only admin, vendor or customer can view all users', status_code=403)

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
	'/refresh-token/',
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
	auth=None,
)
def logout(request, payload: TokenRefreshRequest) -> dict:
	try:
		refresh_token = payload.refresh
		if not refresh_token:
			raise ValueError('Refresh token is required')

		decoded = decode_token(refresh_token, token_type=TokenTypes.REFRESH, verify=True)
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
		raise HttpError(message=f'Failed to logout: {e!s}', status_code=400)


@auth_router.post(
	'/logout-all-devices/',
	response={200: APIResponse, 400: APIResponse},
	url_name='blacklist_tokens',
)
def logout_all_devices(request) -> dict:
	"""
	Logout user from all devices by blacklisting all refresh tokens.
	"""
	user = request.user
	if not user.is_authenticated:
		raise HttpError(message='User is not authenticated', status_code=401)

	blacklist_all_tokens(user)
	return make_response(
		success=True,
		message='User logged out from all devices successfully',
		status_code=200,
	)


@auth_router.post('/restore-account/', response={200: APIResponse, 400: APIResponse})
def restore_account(request, user_id: int = None) -> dict:
	if user_id and user.user_type != UserType.ADMIN:
		raise AuthorizationError(message='Only admin can restore other user accounts', status_code=403)

	user_id = user_id or user.id
	user = get_object_or_404(User, id=user_id)

	try:
		restore_user_and_profile(user)
		return make_response(
			success=True,
			message='User account restored successfully',
			status_code=200,
		)
	except Exception as e:
		raise HttpError(message=f'Failed to restore account: {e!s}', status_code=400)


@auth_router.post('/password-reset-request/', response={200: APIResponse, 400: APIResponse}, auth=None)
def password_reset_request(request, payload: PasswordResetRequest) -> dict:
	"""
	Request a password reset by sending an OTP to the user's email.
	Fails silently if the user does not exist.
	"""
	try:
		user = User.objects.filter(email=payload.email).first()
		if not user:
			return make_response(
				success=True,
				message='If the email exists, a password reset OTP has been sent.',
				status_code=200,
			)

		if not user.is_active or not user.is_verified:
			raise AuthorizationError(message='User is not active or verified', status_code=400)

		try:
			otp = create_otp(user=user, otp_type=OtpType.PASSWORD_RESET)
			suspicious_activity_url = signing_dumps(request, 'password_reset', {'user_id': user.id})
		except Exception as e:
			raise HttpError(message=f'Failed to create OTP: {e!s}', status_code=400)

		# Send the password reset email
		send_email_task.defer(
			user_email=otp.user.email,
			template_name=OtpType.PASSWORD_RESET,
			category='otp',
			subject='Password Reset Request',
			context={
				'otp_code': otp.otp_code,
				'app_name': domain_name,
				'current_year': datetime.now().year,
				'suspicious_activity_url': suspicious_activity_url,
			},
		)

		# Return success response
		return make_response(
			success=True,
			message='a password reset OTP has been sent.',
			status_code=200,
		)
	except Exception as e:
		raise HttpError(message=f'Failed to send password reset OTP: {e!s}', status_code=400)


@auth_router.get('/suspicious-activity/', response={200: APIResponseWithData[dict]}, auth=None)
def suspicious_activity(request, token: str) -> dict:
	"""
	Handle suspicious activity alert by verifying the signed token.
	"""
	try:
		data = verify_signed_data(token)
		user_id = data.get('user_id')
		if not user_id:
			raise HttpError(message='Invalid token: Missing user_id', status_code=400)

		user = get_object_or_404(User, id=user_id)

		blacklist_all_tokens(user)
		return make_data_response(
			status_code=200,
			message='Suspicious activity verified and user logged out from all devices',
			data={'user_id': user.id, 'message': 'User logged out successfully'},
		)
	except Exception as e:
		raise HttpError(message=f'Failed to verify suspicious activity: {e!s}', status_code=400)


@auth_router.post('/password-update/', response={200: APIResponse, 400: APIResponse}, auth=None)
def password_update(request, payload: PasswordResetVerify) -> dict:
	"""
	Update the user's password.
	"""
	user = get_object_or_404(User, email=payload.email)
	success, message = verify_otp(
		user=user,
		otp_code=payload.otp,
		otp_type=OtpType.PASSWORD_RESET,
	)

	if not success:
		return make_response(False, 400, message)

	try:
		user.set_password(payload['password'])
		user.save()
		return make_response(
			success=True,
			message='Password updated successfully',
			status_code=200,
		)
	except Exception as e:
		raise HttpError(message=f'Failed to update password: {e!s}', status_code=400)


@auth_router.post('/account-delete-request/', response={200: APIResponse, 400: APIResponse})
def account_delete_request(request) -> dict:
	"""
	Request to delete the user account by sending an OTP to the user's email.
	Fails silently if the user does not exist.
	"""

	user = request.user
	try:
		otp = create_otp(user=user, otp_type=OtpType.ACCOUNT_DELETE)
		suspicious_activity_url = signing_dumps(request, 'account_delete', {'user_id': user.id})
		send_email_task.defer(
			user_email=otp.user.email,
			template_name=OtpType.ACCOUNT_DELETE,
			category='otp',
			subject='Account Deletion Request',
			context={
				'user_name': user.full_name,
				'otp_code': otp.otp_code,
				'app_name': domain_name,
				'current_year': datetime.now().year,
				'suspicious_activity_url': suspicious_activity_url,
			},
		)
	except Exception as e:
		raise HttpError(message=f'Failed to create OTP: {e!s}', status_code=400)

	return make_response(
		success=True,
		message='If the email exists, an account deletion OTP has been sent.',
		status_code=200,
	)


@auth_router.get('/delete-account/', response={200: APIResponseWithData[dict]})
def account_delete(request, payload: AccountDeleteVerify) -> dict:
	"""
	Handle account deletion request by verifying the OTP and deleting the user account.
	"""
	user = request.user
	success, message = verify_otp(
		user=user,
		otp_code=payload.otp,
		otp_type=OtpType.ACCOUNT_DELETE,
	)
	if not success:
		return make_response(False, 400, message)
	try:
		delete_user_and_profile(user)
		# send account deletion email
		send_email_task.defer(
			user_email=user.email,
			template_name=OtpType.ACCOUNT_DELETION_CONFIRMATION,
			category='otp',
			subject='Account Deleted Successfully',
			context={
				'app_name': domain_name,
				'current_year': datetime.now().year,
			},
		)
		return make_data_response(
			status_code=200,
			message='User account deleted successfully',
			data={'user_id': user.id, 'message': 'User account deleted successfully'},
		)
	except Exception as e:
		raise HttpError(message=f'Failed to delete account: {e!s}', status_code=400)
