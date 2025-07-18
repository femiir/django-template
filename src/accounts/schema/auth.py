from ninja import Field, FilterSchema, ModelSchema, Schema
from pydantic import EmailStr

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
	email: EmailStr
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
	email: str | None = Field(None, q='email__icontains', description='Filter by email')
	full_name: str | None = Field(None, q='full_name__icontains', description='Filter by full name')
	phone_number: str | None = Field(None, q='phone_number__icontains', description='Filter by phone number')
	user_type: UserType | None = Field(None, description='Filter by user type')
	is_active: bool | None = Field(None, description='Filter by active status')
	is_verified: bool | None = Field(None, description='Filter by verification status')

	class Config:
		expression_connector = 'OR'


class AccountDeleteVerify(Schema):
	otp: str
	email: EmailStr
