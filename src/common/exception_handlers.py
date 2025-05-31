from django.http import Http404, JsonResponse
from ninja.errors import (
	AuthenticationError,
	AuthorizationError,
	HttpError,
	ValidationError,
)

from common.schema import make_response


def custom_exception_handler(request, exc):
	# Handle Ninja and Django exceptions with your response schema
	if isinstance(exc, ValidationError):
		return JsonResponse(
			make_response(False, 422, getattr(exc, 'errors', str(exc))).__dict__,
			status=422,
		)
	if isinstance(exc, (AuthenticationError, AuthorizationError)):
		return JsonResponse(make_response(False, 403, str(exc)).__dict__, status=403)
	if isinstance(exc, HttpError):
		return JsonResponse(
			make_response(False, exc.status_code, str(exc)).__dict__,
			status=exc.status_code,
		)
	if isinstance(exc, Http404):
		return JsonResponse(make_response(False, 404, 'Not found').__dict__, status=404)
	# Catch-all for any other exception
	return JsonResponse(make_response(False, 500, str(exc)).__dict__, status=500)
