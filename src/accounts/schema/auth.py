from ninja import ModelSchema, Schema, FilterSchema
from pydantic import EmailStr
from ninja import FilterSchema, Field
from typing import Optional

from accounts.models import AdminProfile, CustomerProfile, User, UserType, VendorProfile

_exclude = ['id', 'user', 'created_at', 'modified', 'deleted_at', 'is_deleted']


class UserIn(Schema):
	email: EmailStr
	password: str
	user_type: str
	full_name: str
	phone_number: str
	user_type: UserType


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


class PasswordResetRequest(Schema):
	email: EmailStr


class PasswordResetVerify(Schema):
	otp: str
	new_password: str


class CustomerProfileOut(ModelSchema):
	class Meta:
		model = CustomerProfile
		exclude = _exclude


class VendorProfileOut(ModelSchema):
	class Meta:
		model = VendorProfile
		exclude = _exclude


class AdminProfileOut(ModelSchema):
	class Meta:
		model = AdminProfile
		exclude = _exclude


class UserOut(ModelSchema):
	profile: CustomerProfileOut | VendorProfileOut | AdminProfileOut = None

	class Meta:
		model = User
		fields = ['id', 'email', 'full_name', 'phone_number', 'user_type']
		orm_mode = True


class UserUpdate(Schema):
	email: EmailStr
	full_name: str
	phone_number: str
	profile: CustomerProfileOut | VendorProfileOut | AdminProfileOut | None = None

class UserFilter(FilterSchema):
	email: Optional[str] = Field(None, q='email__icontains', description="Filter by email")
	full_name: Optional[str] = Field(None, q='full_name__icontains', description="Filter by full name")
	phone_number: Optional[str] = Field(None, q='phone_number__icontains', description="Filter by phone number")
	user_type: Optional[UserType] = Field(None, description="Filter by user type")
	is_active: Optional[bool] = Field(None, description="Filter by active status")
	is_verified: Optional[bool] = Field(None, description="Filter by verification status")

	class Config:
		expression_connector = 'OR'
