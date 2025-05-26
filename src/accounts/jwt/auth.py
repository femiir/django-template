from django.http import HttpRequest
from ninja.security import HttpBearer
from ninja.security.http import DecodeError

from .token import get_user_from_token


class HttpJwtAuth(HttpBearer):
    async def authenticate(self, request: HttpRequest, token: str) -> bool:
        token = self.decode_authorization(request.headers["Authorization"])
        user = await get_user_from_token(token)
        if user.is_authenticated:
            request.user = user
        return True

    def decode_authorization(self, value: str) -> str:
        parts = value.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise DecodeError("Invalid Authorization header")

        token = parts[1]
        return token
