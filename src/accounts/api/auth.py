
from django.contrib.auth import authenticate
from django.contrib.auth.signals import user_logged_in
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from jwt.exceptions import PyJWTError
from ninja import Router
from ninja.errors import AuthenticationError, HttpError

from accounts.jwt.auth import HttpJwtAuth
from accounts.jwt.token import (
    get_access_token_for_user,
    get_access_token_from_refresh_token,
    get_refresh_token_for_user,
)
from accounts.models import User, UserType
from accounts.schema.auth import (
    Login,
    Token,
    TokenRefreshRequest,
    TokenResponse,
    UserIn,
    UserOut,
    PasswordResetRequest,
    PasswordResetVerify,
)


auth_router = Router(tags=["Auth"], auth=None)



@auth_router.post("/register/", response=Token, url_name="register")
def register(request, payload: UserIn) -> dict:
    try:
        user = User.objects.create_user(**payload.model_dump())
    except Exception as e:
        raise HttpError(message=str(e), status_code=400) from e
    
    refresh_token, _ = get_refresh_token_for_user(user)
    access_token, _ = get_access_token_for_user(user)
    return {"refresh": refresh_token, "access": access_token}



# @auth_router.get("all-users/", response={200: OwnarsResponse, 403: OwnarsResponse}, auth=HttpJwtAuth())
# def get_all_users(request: HttpRequest, user_type: str = None) -> dict:
#     if request.user.user_type != UserType.ADMIN:
#         return 403, {"success": False, "status_code": 403, "message": "You are not authorized to view this page"}
#     if user_type:
#         users = User.objects.filter(user_type=user_type)
#     else:
#         users = User.objects.all()
#         # remove the guardian AnonymousUser
#         users = [user for user in users if user.email != "AnonymousUser"]
#     data = [UserOut.from_orm(user).model_dump() for user in users]
#     return 200, {"success": True, "status_code": 200, "message": data}

