from ninja import ModelSchema, Schema

from ..models import Otp, OtpType



class OtpValidateIn(Schema):
	email: str
	otp_code: str
	otp_type: OtpType

