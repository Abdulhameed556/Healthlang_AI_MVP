"""FastAPI providers for auth use-cases."""
from fastapi import Depends

from backend.src.application.auth.use_cases.get_google_oauth_url import GetGoogleOAuthUrl
from backend.src.application.auth.use_cases.login_with_email import LoginWithEmail
from backend.src.application.auth.use_cases.login_with_google import LoginWithGoogle
from backend.src.application.auth.use_cases.logout import Logout
from backend.src.application.auth.dependencies.infrastructure import (
    get_password_reset_email_sender,
)
from backend.src.application.auth.ports.password_reset_email import (
    IPasswordResetEmailSender,
)
from backend.src.application.auth.use_cases.complete_password_reset import (
    CompletePasswordReset,
)
from backend.src.application.auth.use_cases.request_password_reset import (
    RequestPasswordReset,
)
from backend.src.application.auth.use_cases.refresh_token import RefreshToken
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.core.config import settings
from backend.src.domain.auth.repositories import (
    IPasswordResetRepository,
    IUserSessionRepository,
)
from backend.src.domain.invitations.repositories import IInvitationRepository
from backend.src.domain.departments.repositories import IDepartmentRepository
from backend.src.domain.users.repositories import IUserRepository
from backend.src.infrastructure.database.dependencies import (
    get_invitation_repository,
    get_department_repository,
    get_password_reset_repository,
    get_unit_of_work,
    get_user_repository,
    get_user_session_repository,
)
from backend.src.infrastructure.external.google.google_oauth_client import GoogleOAuthClient


def get_google_oauth_client() -> GoogleOAuthClient:
    return GoogleOAuthClient(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        redirect_uri=settings.google_redirect_uri,
    )


def get_login_with_email(
    user_repository: IUserRepository = Depends(get_user_repository),
    invitation_repository: IInvitationRepository = Depends(get_invitation_repository),
    department_repository: IDepartmentRepository = Depends(get_department_repository),
    session_repository: IUserSessionRepository = Depends(get_user_session_repository),
) -> LoginWithEmail:
    return LoginWithEmail(
        user_repository=user_repository,
        invitation_repository=invitation_repository,
        department_repository=department_repository,
        session_repository=session_repository,
    )


def get_login_with_google(
    google_oauth_client: GoogleOAuthClient = Depends(get_google_oauth_client),
    user_repository: IUserRepository = Depends(get_user_repository),
    invitation_repository: IInvitationRepository = Depends(get_invitation_repository),
    department_repository: IDepartmentRepository = Depends(get_department_repository),
    session_repository: IUserSessionRepository = Depends(get_user_session_repository),
) -> LoginWithGoogle:
    return LoginWithGoogle(
        google_oauth_client=google_oauth_client,
        user_repository=user_repository,
        invitation_repository=invitation_repository,
        department_repository=department_repository,
        session_repository=session_repository,
    )


def get_google_oauth_url_use_case() -> GetGoogleOAuthUrl:
    return GetGoogleOAuthUrl()


def get_logout(
    session_repository: IUserSessionRepository = Depends(get_user_session_repository),
) -> Logout:
    return Logout(session_repository=session_repository)


def get_refresh_token(
    user_repository: IUserRepository = Depends(get_user_repository),
    session_repository: IUserSessionRepository = Depends(get_user_session_repository),
) -> RefreshToken:
    return RefreshToken(
        user_repository=user_repository,
        session_repository=session_repository,
    )


def get_request_password_reset(
    user_repository: IUserRepository = Depends(get_user_repository),
    password_reset_repository: IPasswordResetRepository = Depends(
        get_password_reset_repository
    ),
    password_reset_email_sender: IPasswordResetEmailSender = Depends(
        get_password_reset_email_sender
    ),
    unit_of_work: IUnitOfWork = Depends(get_unit_of_work),
) -> RequestPasswordReset:
    return RequestPasswordReset(
        user_repository=user_repository,
        password_reset_repository=password_reset_repository,
        password_reset_email_sender=password_reset_email_sender,
        unit_of_work=unit_of_work,
    )


def get_complete_password_reset(
    user_repository: IUserRepository = Depends(get_user_repository),
    password_reset_repository: IPasswordResetRepository = Depends(
        get_password_reset_repository
    ),
    session_repository: IUserSessionRepository = Depends(get_user_session_repository),
    unit_of_work: IUnitOfWork = Depends(get_unit_of_work),
) -> CompletePasswordReset:
    return CompletePasswordReset(
        user_repository=user_repository,
        password_reset_repository=password_reset_repository,
        session_repository=session_repository,
        unit_of_work=unit_of_work,
    )
