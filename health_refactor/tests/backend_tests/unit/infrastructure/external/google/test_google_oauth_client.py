"""Unit tests: infrastructure/external/google/google_oauth_client.py"""
import httpx
import pytest
import respx

from backend.src.domain.auth.exceptions import GoogleOAuthExchangeError
from backend.src.infrastructure.external.google.google_oauth_client import (
    GOOGLE_TOKEN_URL,
    GOOGLE_USERINFO_URL,
    GoogleOAuthClient,
)


@pytest.fixture()
def client() -> GoogleOAuthClient:
    return GoogleOAuthClient(
        client_id="test-client-id",
        client_secret="test-secret",
        redirect_uri="http://localhost:3000/auth/callback/google",
    )


def test_get_authorization_url_contains_google_host(client: GoogleOAuthClient) -> None:
    url = client.get_authorization_url()
    assert "accounts.google.com" in url
    assert "client_id=test-client-id" in url


@respx.mock
@pytest.mark.asyncio
async def test_fetch_user_info_exchanges_code(client: GoogleOAuthClient) -> None:
    respx.post(GOOGLE_TOKEN_URL).mock(
        return_value=httpx.Response(
            200,
            json={"access_token": "at", "token_type": "Bearer"},
        )
    )
    respx.get(GOOGLE_USERINFO_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "email": "user@example.com",
                "given_name": "Sam",
                "family_name": "Test",
                "sub": "google-123",
            },
        )
    )

    info = await client.fetch_user_info("auth-code-xyz")

    assert info.email == "user@example.com"
    assert info.given_name == "Sam"
    assert info.sub == "google-123"


@pytest.mark.asyncio
async def test_fetch_user_info_rejects_empty_code(client: GoogleOAuthClient) -> None:
    with pytest.raises(GoogleOAuthExchangeError, match="code"):
        await client.fetch_user_info("   ")
