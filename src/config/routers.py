# ruff: isort: skip_file
from accounts.api.auth import auth_router
from otp.api.otp import otp_router

router_list = [
    ("/auth/", auth_router),
    ("/otp/", otp_router),
]

