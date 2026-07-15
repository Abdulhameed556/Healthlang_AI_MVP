"""Use-case: build Google OAuth authorization URL for the product SPA."""
from backend.src.application.auth.results.google_oauth_url import GoogleOAuthUrlResult
from backend.src.core.config import settings
from backend.src.domain.auth.exceptions import OAuthNotConfiguredError
from backend.src.infrastructure.external.google.google_oauth_client import GoogleOAuthClient


class GetGoogleOAuthUrl:
    def execute(self) -> GoogleOAuthUrlResult:
        if not settings.google_oauth_configured:
            raise OAuthNotConfiguredError("Google OAuth is not configured")

        client = GoogleOAuthClient(
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            redirect_uri=settings.google_redirect_uri,
        )
        return GoogleOAuthUrlResult(oauth_url=client.get_authorization_url())
