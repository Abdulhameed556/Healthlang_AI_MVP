"""Unit tests: auth DI providers."""
from unittest.mock import MagicMock

from backend.src.application.auth import dependencies as deps
from backend.src.application.auth.use_cases.complete_password_reset import (
    CompletePasswordReset,
)
from backend.src.application.auth.use_cases.login_with_email import LoginWithEmail
from backend.src.application.auth.use_cases.logout import Logout
from backend.src.application.auth.use_cases.request_password_reset import (
    RequestPasswordReset,
)


class TestProviders:
    def test_build_login_use_case(self, monkeypatch):
        monkeypatch.setattr(
            deps,
            "get_user_repository",
            lambda db=None: MagicMock(),
        )
        monkeypatch.setattr(
            deps,
            "get_invitation_repository",
            lambda db=None: MagicMock(),
        )
        monkeypatch.setattr(
            deps,
            "get_department_repository",
            lambda db=None: MagicMock(),
        )
        monkeypatch.setattr(
            deps,
            "get_user_session_repository",
            lambda db=None: MagicMock(),
        )
        use_case = deps.get_login_with_email(
            user_repository=MagicMock(),
            invitation_repository=MagicMock(),
            department_repository=MagicMock(),
            session_repository=MagicMock(),
        )
        assert isinstance(use_case, LoginWithEmail)

    def test_build_logout_use_case(self):
        use_case = deps.get_logout(
            session_repository=MagicMock(),
        )
        assert isinstance(use_case, Logout)

    def test_build_request_password_reset_use_case(self):
        use_case = deps.get_request_password_reset(
            user_repository=MagicMock(),
            password_reset_repository=MagicMock(),
            password_reset_email_sender=MagicMock(),
            unit_of_work=MagicMock(),
        )
        assert isinstance(use_case, RequestPasswordReset)

    def test_build_complete_password_reset_use_case(self):
        use_case = deps.get_complete_password_reset(
            user_repository=MagicMock(),
            password_reset_repository=MagicMock(),
            session_repository=MagicMock(),
            unit_of_work=MagicMock(),
        )
        assert isinstance(use_case, CompletePasswordReset)
