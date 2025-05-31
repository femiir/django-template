# src/common/responses.py

from typing import Any, Optional, Generic, TypeVar
from pydantic.generics import GenericModel
from ninja import Schema


# Base schema for all responses
class APIResponse(Schema):
	success: bool = False
	status_code: int
	message: Optional[Any] = None


# Generic schema with a `data` field for responses with payloads
T = TypeVar('T')


class APIResponseWithData(GenericModel, Generic[T]):
	success: bool = False
	status_code: int
	message: Optional[Any] = None
	data: Optional[T] = None


# Helper function to generate APIResponse
def make_response(success: bool, status_code: int, message: Any = None) -> APIResponse:
	return APIResponse(success=success, status_code=status_code, message=message)


# Helper function to generate APIResponseWithData
def make_data_response(
	data: T, status_code: int = 200, message: Any = None
) -> APIResponseWithData[T]:
	return APIResponseWithData(
		success=True, status_code=status_code, message=message, data=data
	)
