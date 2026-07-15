"""Google OAuth2 client (authorization URL + token + userinfo)."""
import logging
import secrets
from urllib.parse import urlencode

from authlib.integrations.httpx_client import AsyncOAuth2Client

from backend.src.application.auth.ports.google_oauth import GoogleUserInfo
from backend.src.domain.auth.exceptions import GoogleOAuthExchangeError

logger = logging.getLogger(__name__)

GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
GOOGLE_SCOPES = "openid email profile"


class GoogleOAuthClient:
    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    def get_authorization_url(self, *, state: str | None = None) -> str:
        oauth_state = state or secrets.token_urlsafe(32)
        query = urlencode(
            {
                "client_id": self._client_id,
                "redirect_uri": self._redirect_uri,
                "response_type": "code",
                "scope": GOOGLE_SCOPES,
                "state": oauth_state,
                "access_type": "offline",
                "prompt": "consent",
            }
        )
        return f"{GOOGLE_AUTHORIZE_URL}?{query}"

    async def fetch_user_info(self, code: str) -> GoogleUserInfo:
        if not code or not code.strip():
            raise GoogleOAuthExchangeError("Authorization code is required")

        try:
            async with AsyncOAuth2Client(
                client_id=self._client_id,
                client_secret=self._client_secret,
                redirect_uri=self._redirect_uri,
            ) as client:
                await client.fetch_token(
                    GOOGLE_TOKEN_URL,
                    code=code.strip(),
                )
                response = await client.get(GOOGLE_USERINFO_URL)
                response.raise_for_status()
                data = response.json()
        except GoogleOAuthExchangeError:
            raise
        except Exception as exc:
            logger.warning("google oauth exchange failed: %s", exc)
            raise GoogleOAuthExchangeError(
                "Failed to authenticate with Google"
            ) from exc

        email = (data.get("email") or "").strip()
        if not email:
            raise GoogleOAuthExchangeError("Google did not return an email address")

        return GoogleUserInfo(
            email=email,
            given_name=(data.get("given_name") or "").strip(),
            family_name=(data.get("family_name") or "").strip(),
            sub=(data.get("sub") or "").strip(),
        )
