# GET /api/v1/auth/google/url

## URL

**Path:** `/api/v1/auth/google/url`

**Full URL:** `<base>/api/v1/auth/google/url`

| Environment | Base URL (`<base>`) | Example full URL |
|-------------|---------------------|------------------|
| Local | `http://localhost:8000` | `http://localhost:8000/api/v1/auth/google/url` |
| Staging | `https://api-staging.example.com` | `https://api-staging.example.com/api/v1/auth/google/url` |
| Production | `https://api.example.com` | `https://api.example.com/api/v1/auth/google/url` |

## Summary

Returns the Google OAuth authorization URL for the product SPA to redirect the user.
The SPA receives an authorization `code` on its callback URL and exchanges it via
[google-login.md](google-login.md).

## Auth

- Required: no

## Request

- No body
- No query parameters required

## Response

### 200 OK

```json
{
  "message": "OAuth URL ready",
  "status_code": 200,
  "error": false,
  "data": {
    "oauth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=...&response_type=code&scope=openid+email+profile&state=..."
  }
}
```

Redirect the browser to `data.oauth_url`. After Google sign-in, Google redirects to
`GOOGLE_REDIRECT_URI` (typically the SPA callback) with `?code=...&state=...`.

### Error responses

| Status | When | Sample `message` |
|--------|------|------------------|
| 503 | Google OAuth env vars not set on server | `Google OAuth is not configured` |

## Frontend notes

- **Backend env:** `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`
  (see `.env.example`). Redirect URI must match Google Cloud Console exactly.
- **Typical flow:**
  1. `GET /api/v1/auth/google/url`
  2. `window.location.href = data.oauth_url`
  3. SPA callback page reads `code` from query string
  4. `POST /api/v1/auth/google` with `code` (and `invitation_token` if on invite page)
- Do not expose `GOOGLE_CLIENT_SECRET` in the frontend; only the backend uses it.

## Related

- [google-login.md](google-login.md) — exchange `code` for JWT
- [login.md](login.md) — email/password alternative
- Code: `backend/src/presentation/api/v1/auth/endpoints/google_oauth.py`
- Use-case: `backend/src/application/auth/use_cases/get_google_oauth_url.py`
