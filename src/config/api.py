# ruff: isort: skip_file
from ninja import NinjaAPI
from ninja.errors import (
	AuthenticationError,
	AuthorizationError,
	ValidationError,
	HttpError,
)
from django.http import Http404
from common.exception_handlers import custom_exception_handler

from ninja.pagination import RouterPaginated

from .routers import router_list

api = NinjaAPI(
	title='Backend API',
	version='1.0.0',
	description='Backend API Documentation',
	docs_url='/',
	urls_namespace='backend',
	default_router=RouterPaginated(),
)

api.add_exception_handler(AuthenticationError, custom_exception_handler)
api.add_exception_handler(AuthorizationError, custom_exception_handler)
api.add_exception_handler(ValidationError, custom_exception_handler)
api.add_exception_handler(HttpError, custom_exception_handler)
api.add_exception_handler(Http404, custom_exception_handler)
api.add_exception_handler(Exception, custom_exception_handler)

for path, router in router_list:
	api.add_router(path, router)
