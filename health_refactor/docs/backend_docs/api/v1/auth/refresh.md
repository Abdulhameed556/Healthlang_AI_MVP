# POST /api/v1/auth/refresh

## URL

**Path:** `/api/v1/auth/refresh`

**Full URL:** `<base>/api/v1/auth/refresh`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/auth/refresh` |
| Staging | `https://api-staging.example.com/api/v1/auth/refresh` |
| Production | `https://api.example.com/api/v1/auth/refresh` |

## Summary

Exchanges a valid **refresh token** (from [login](login.md) or [google-login](google-login.md))
for a new access JWT and a **rotated** refresh token.

Refresh tokens expire after **`JWT_REFRESH_TOKEN_EXPIRE_DAYS`** (default **3 days**).

Public route — no `Authorization` header required.

## Auth

- Required: no
- Send the refresh token in the JSON body

## Request

```json
{
  "refresh_token": "opaque-refresh-token-from-login"
}
```

## Response (200)

```json
{
  "message": "Token refreshed successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "access_token": "new-jwt",
    "refresh_token": "new-rotated-refresh-token"
  }
}
```

Replace stored tokens with both values from `data`. The previous refresh token is invalidated after rotation.

## Errors

| Status | When |
|--------|------|
| 401 | Missing, unknown, or expired refresh token |
| 403 | User account no longer active |
| 422 | Missing `refresh_token` in body |

## Frontend flow

1. On login, store `access_token` and `refresh_token`.
2. Call APIs with `Authorization: Bearer <access_token>`.
3. On **401** (expired access), call `POST /auth/refresh` with `refresh_token`.
4. Update stored tokens and retry the failed request.
5. On logout, call [logout](logout.md) with the current access token (invalidates the whole session).

## Code

- Endpoint: `backend/src/presentation/api/v1/auth/endpoints/token_refresh.py`
- Use-case: `backend/src/application/auth/use_cases/refresh_token.py`
