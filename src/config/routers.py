# ruff: isort: skip_file
from accounts.api.auth import auth_router

router_list = [
    ("/auth/", auth_router),
]

