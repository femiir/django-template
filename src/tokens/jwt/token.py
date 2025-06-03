from datetime import datetime
from enum import Enum
from json import JSONEncoder
from typing import Any
from uuid import UUID, uuid4

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from django.utils.timezone import make_aware
from jwt import ExpiredSignatureError, InvalidKeyError, InvalidTokenError, PyJWTError
from ninja.errors import AuthenticationError

from tokens.models import BlacklistedToken, TrackedToken

User = get_user_model()


class TokenTypes(str, Enum):
	ACCESS = 'access'
	REFRESH = 'refresh'


class TokenUserEncoder(DjangoJSONEncoder):
	def default(self, o: Any) -> Any:
		if isinstance(o, UUID):
			return str(o)

		return super().default(o)


# DEPRECATED: Use get_obtain_token_pair() instead
def get_refresh_token_for_user(user: AbstractBaseUser) -> tuple[str, dict]:
	payload = get_token_payload_for_user(user)
	token, payload_data = encode_token(
		payload, TokenTypes.REFRESH, json_encoder=TokenUserEncoder
	)

	return token, payload_data


# DEPRECATED: Use get_obtain_token_pair() instead
def get_access_token_for_user(user: AbstractBaseUser) -> tuple[str, dict]:
	payload = get_token_payload_for_user(user)
	token, payload_data = encode_token(
		payload, TokenTypes.ACCESS, json_encoder=TokenUserEncoder
	)
	return token, payload_data


def get_token_payload_for_user(user: AbstractBaseUser) -> dict:
	return {
		claim: getattr(user, user_attr)
		if isinstance(user_attr, str)
		else user_attr(user)
		for claim, user_attr in settings.TOKEN_CLAIM_USER_ATTRIBUTE_MAP.items()
	}


def get_access_token_from_refresh_token(refresh_token: str) -> tuple[str, dict]:
	decoded = decode_token(refresh_token, token_type=TokenTypes.REFRESH, verify=True)
	payload = {
		claim: decoded.get(claim) for claim in settings.TOKEN_CLAIM_USER_ATTRIBUTE_MAP
	}
	return encode_token(payload, TokenTypes.ACCESS)


def encode_token(
	payload: dict,
	token_type: TokenTypes,
	jti: UUID | None = None,
	json_encoder: type[JSONEncoder] | None = None,
	**additional_headers: Any,
) -> tuple[str, dict]:
	now = timezone.now()
	if token_type == TokenTypes.REFRESH:
		expiry = now + settings.JWT_REFRESH_TOKEN_LIFETIME
	else:
		expiry = now + settings.JWT_ACCESS_TOKEN_LIFETIME

	payload_data = {
		**payload,
		'jti': jti or uuid4().hex,
		'exp': int(expiry.timestamp()),
		'iat': int(now.timestamp()),
		'token_type': token_type,
	}

	return (
		jwt.encode(
			payload_data,
			settings.SECRET_KEY,
			algorithm=settings.JWT_ALGORITHM,
			headers=additional_headers,
			json_encoder=json_encoder,
		),
		payload_data,
	)


def decode_token(token: str, token_type: TokenTypes, verify: bool = True) -> dict:
	if verify is True:
		decoded = jwt.decode(
			token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
		)
		_verify_exp(decoded)
		_verify_jti(decoded)
		_verify_token_type(decoded, token_type)
	else:
		decoded = jwt.get_unverified_header(token)
	return decoded


def _verify_exp(payload: dict) -> None:
	now = timezone.now()
	token_expiry_unix_time = payload['exp']
	token_expiry = timezone.make_aware(datetime.fromtimestamp(token_expiry_unix_time))
	if now >= token_expiry:
		raise ExpiredSignatureError('JWT has expired.')


def _verify_jti(payload: dict) -> None:
	jti = payload.get('jti')
	user = payload.get('user_id')

	if not jti and not user:
		raise InvalidKeyError('Missing key jti or user.')
	jti = TrackedToken.hasher(jti)
	if BlacklistedToken.all_objects.filter(user=user, token__jti=jti).exists():
		raise InvalidTokenError('Token has been blacklisted.')


def _verify_token_type(payload: dict, token_type: TokenTypes) -> None:
	if 'token_type' not in payload:
		raise InvalidKeyError('Missing token type in JWT.')
	if payload['token_type'] != token_type:
		raise InvalidTokenError('Incorrect token type in JWT.')


def set_token_claims_to_user(user: AbstractBaseUser, token: dict) -> None:
	for claim, user_attribute in settings.TOKEN_CLAIM_USER_ATTRIBUTE_MAP.items():
		if isinstance(user_attribute, str):
			setattr(user, user_attribute, token.get(claim))
		else:
			setattr(user, claim, token.get(claim))


def get_user_from_token(token: str) -> AbstractBaseUser:
	try:
		access_token = decode_token(token, token_type=TokenTypes.ACCESS, verify=True)
	except PyJWTError as e:
		raise AuthenticationError(e)

	user_id = access_token.get('user_id')
	if user_id is None:
		raise AuthenticationError('User ID not found in token.')

	try:
		user = User.objects.get(id=user_id)
	except User.DoesNotExist:
		raise AuthenticationError('User not found.')

	set_token_claims_to_user(user, access_token)

	return user


def get_obtain_token_pair(user: AbstractBaseUser) -> tuple[str, str]:
	"""
	Get a pair of tokens (access and refresh) for the user.
	"""
	payload = get_token_payload_for_user(user)
	_jti = uuid4().hex
	access_token, access_payload = encode_token(
		payload=payload,
		token_type=TokenTypes.ACCESS,
		jti=_jti,
		json_encoder=TokenUserEncoder,
	)
	refresh_token, refresh_payload = encode_token(
		payload=payload,
		token_type=TokenTypes.REFRESH,
		jti=_jti,
		json_encoder=TokenUserEncoder,
	)
	# Create tracked token

	try:
		create_tracked_token(
			user,
			jti=_jti,
			exp=refresh_payload['exp'],
			refresh_token=refresh_token,
			access_token=access_token,
		)
		# If the tracked token is created successfully, return the tokens
		return {
			'access_token': access_token,
			'refresh_token': refresh_token,
			'access_payload': access_payload,
			'refresh_payload': refresh_payload,
		}
	except (ValueError, TypeError) as e:
		raise ValueError(f'Failed to create tracked token: {e!s}')


def create_tracked_token(
	user, jti: str, exp: int, refresh_token: str, access_token: str
) -> TrackedToken:
	"""
	Create a tracked token for the user.
	"""
	jti = TrackedToken.hasher(jti)
	refresh_token = TrackedToken.hasher(refresh_token)
	access_token = TrackedToken.hasher(access_token)

	# Convert Unix timestamp to a timezone-aware datetime object
	_exp = make_aware(datetime.fromtimestamp(exp))
	return TrackedToken.objects.get_or_create(
		user=user,
		jti=jti,
		exp=_exp,
		refresh_token=refresh_token,
		access_token=access_token,
	)


def create_blacklisted_token(user, token: TrackedToken) -> BlacklistedToken:
	"""
	Create a blacklisted token for the user.
	"""
	return BlacklistedToken.objects.create(user=user, token=token)


def blacklist_token(user: AbstractBaseUser, token: str) -> None:
	"""
	Blacklist a token for the user.
	"""
	# Decode the token to extract the jti
	decoded = decode_token(token, token_type=TokenTypes.REFRESH, verify=True)
	jti = decoded.get('jti')

	
	if not jti:
		raise ValueError('Invalid token: Missing jti')
	jti = TrackedToken.hasher(jti)
	tracked_token = TrackedToken.all_objects.filter(user=user, jti=jti).first()
	if tracked_token:
		create_blacklisted_token(user, tracked_token)
		tracked_token.soft_delete()

	else:
		raise ValueError('Token not found in tracked tokens')
