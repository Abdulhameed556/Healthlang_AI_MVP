# POST /admin/api/v1/auth/logout

## URL

**Path:** `/admin/api/v1/auth/logout`

**Full URL (local):** `http://localhost:8000/admin/api/v1/auth/logout`

## Summary

Invalidates the current admin session so the access token can no longer be used,
even before its 60-minute expiry. Admin has no refresh token.

## Auth

```http
Authorization: Bearer <access_token>
```

## Request

- No body

## Response (200)

Returned directly (admin success responses are not enveloped):

```json
{ "message": "Logged out" }
```

## Errors

| Status | When |
|--------|------|
| 401 | Missing/invalid admin Bearer token |

## Frontend notes

1. Call `POST /auth/logout` with the stored `access_token`.
2. Clear the `access_token` from memory/storage on success.
3. Redirect to the login screen.

**See also:** [login.md](login.md)

## Code

- Endpoint: `admin/src/presentation/api/v1/auth/endpoints/logout.py`
- Use-case: `admin/src/application/auth/use_cases/logout.py`
