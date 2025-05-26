# ruff: isort: skip_file
from ninja import NinjaAPI
from ninja.errors import AuthenticationError, ValidationError
from django.http import Http404

from ninja.pagination import RouterPaginated
from .routers import router_list

api = NinjaAPI(
    title="Ownars API",
    version="1.0.0",
    description="Ownars API Documentation",
    docs_url="/",
    urls_namespace="ownars",
    default_router=RouterPaginated(),
)


for path, router in router_list:
    api.add_router(path, router)
