from datetime import datetime
from enum import Enum
from json import JSONEncoder
from typing import Any, Optional, Tuple
from uuid import UUID, uuid4

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from jwt import (ExpiredSignatureError, InvalidKeyError, InvalidTokenError,
                 PyJWTError)
from ninja.errors import AuthenticationError


User = get_user_model()


class TokenTypes(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenUserEncoder(DjangoJSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, UUID):
            return str(o)

        return super().default(o)


def get_refresh_token_for_user(user: AbstractBaseUser) -> Tuple[str, dict]:
    payload = get_token_payload_for_user(user)
    return encode_token(payload, TokenTypes.REFRESH, json_encoder=TokenUserEncoder)


def get_access_token_for_user(user: AbstractBaseUser) -> Tuple[str, dict]:
    payload = get_token_payload_for_user(user)
    return encode_token(payload, TokenTypes.ACCESS, json_encoder=TokenUserEncoder)


def get_token_payload_for_user(user: AbstractBaseUser) -> dict:
    return {
        claim: getattr(user, user_attr) if isinstance(
            user_attr, str) else user_attr(user)
        for claim, user_attr in settings.TOKEN_CLAIM_USER_ATTRIBUTE_MAP.items()
    }


def get_access_token_from_refresh_token(refresh_token: str) -> Tuple[str, dict]:
    decoded = decode_token(
        refresh_token, token_type=TokenTypes.REFRESH, verify=True)
    payload = {claim: decoded.get(claim)
               for claim in settings.TOKEN_CLAIM_USER_ATTRIBUTE_MAP}
    return encode_token(payload, TokenTypes.ACCESS)


def encode_token(
    payload: dict, token_type: TokenTypes, json_encoder: Optional[type[JSONEncoder]] = None, **additional_headers: Any
) -> Tuple[str, dict]:
    now = timezone.now()
    if token_type == TokenTypes.REFRESH:
        expiry = now + settings.JWT_REFRESH_TOKEN_LIFETIME
    else:
        expiry = now + settings.JWT_ACCESS_TOKEN_LIFETIME

    payload_data = {
        **payload,
        "jti": uuid4().hex,
        "exp": int(expiry.timestamp()),
        "iat": int(now.timestamp()),
        "token_type": token_type,
    }

    return (
        jwt.encode(
            payload_data,
            settings.SECRET_KEY,
            algorithm="HS256",
            headers=additional_headers,
            json_encoder=json_encoder,
        ),
        payload_data,
    )


def decode_token(token: str, token_type: TokenTypes, verify: bool = True) -> dict:
    if verify is True:
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        _verify_exp(decoded)
        _verify_jti(decoded)
        _verify_token_type(decoded, token_type)
    else:
        decoded = jwt.get_unverified_header(token)
    return decoded


def _verify_exp(payload: dict) -> None:
    now = timezone.now()
    token_expiry_unix_time = payload["exp"]
    token_expiry = timezone.make_aware(
        datetime.fromtimestamp(token_expiry_unix_time))
    if now >= token_expiry:
        raise ExpiredSignatureError("JWT has expired.")


def _verify_jti(payload: dict) -> None:
    if "jti" not in payload:
        raise InvalidKeyError("Invalid jti claim in JWT.")


def _verify_token_type(payload: dict, token_type: TokenTypes) -> None:
    if "token_type" not in payload:
        raise InvalidKeyError("Missing token type in JWT.")
    if payload["token_type"] != token_type:
        raise InvalidTokenError("Incorrect token type in JWT.")


def set_token_claims_to_user(user: AbstractBaseUser, token: dict) -> None:
    for claim, user_attribute in settings.TOKEN_CLAIM_USER_ATTRIBUTE_MAP.items():
        if isinstance(user_attribute, str):
            setattr(user, user_attribute, token.get(claim))
        else:
            setattr(user, claim, token.get(claim))


async def get_user_from_token(token: str) -> AbstractBaseUser:
    try:
        access_token = decode_token(
            token, token_type=TokenTypes.ACCESS, verify=True)
    except PyJWTError as e:
        raise AuthenticationError(e)
    
    user_id = access_token.get("user_id")
    if user_id is None:
        raise AuthenticationError("User ID not found in token.")
    
    try:
        user = await User.objects.aget(id=user_id)
    except User.DoesNotExist:
        raise AuthenticationError("User not found.")
    
    set_token_claims_to_user(user, access_token)

    return user
