from typing import Optional
from ninja import Schema

# from accounts.models import User, VendorProfile, CustomerProfile
from pydantic import EmailStr


class UserIn(Schema):
    email: EmailStr
    password: str
    user_type: str
    full_name: str
    phone_number: str


class Login(Schema):
    email: EmailStr
    password: str


class Token(Schema):
    access: str
    refresh: str


class TokenResponse(Schema):
    access: str


class TokenRefreshRequest(Schema):
    refresh: str


class UserOut(Schema):
    id: int
    email: EmailStr
    user_type: str
    full_name: str
    phone_number: Optional[str]
    # groups: Any
    # user_permissions: Any


class PasswordResetRequest(Schema):
    email: EmailStr


class PasswordResetVerify(Schema):
    otp: str
    new_password: str
