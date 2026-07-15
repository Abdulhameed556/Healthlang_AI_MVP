"""Auth dependency wiring."""
from backend.src.application.auth.dependencies.providers import (
    get_complete_password_reset,
    get_google_oauth_url_use_case,
    get_invitation_repository,
    get_login_with_email,
    get_login_with_google,
    get_logout,
    get_department_repository,
    get_refresh_token,
    get_request_password_reset,
    get_user_repository,
    get_user_session_repository,
)

__all__ = [
    "get_complete_password_reset",
    "get_google_oauth_url_use_case",
    "get_invitation_repository",
    "get_login_with_email",
    "get_login_with_google",
    "get_logout",
    "get_department_repository",
    "get_refresh_token",
    "get_request_password_reset",
    "get_user_repository",
    "get_user_session_repository",
]
