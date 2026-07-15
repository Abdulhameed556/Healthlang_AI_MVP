# POST /api/v1/auth/logout

## URL

**Path:** `/api/v1/auth/logout`

**Full URL:** `<base>/api/v1/auth/logout`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/auth/logout` |
| Staging | `https://api-staging.example.com/api/v1/auth/logout` |
| Production | `https://api.example.com/api/v1/auth/logout` |

## Summary

Invalidates the current Bearer access token by setting `invalidated_at` on its
`user_sessions` row. Access and refresh tokens for that session are invalidated.
After logout, protected routes reject that token even if the JWT has not expired yet.

Idempotent: calling logout again with the same token still returns **200**.

## Auth

```http
Authorization: Bearer <access_token>
```

Optional `X-Organization-Id` is accepted but does not affect logout (the session is
invalidated regardless). See [organization-context.md](organization-context.md).

## Request

- No body

## Response (200)

```json
{
  "message": "Logout successful",
  "status_code": 200,
  "error": false,
  "data": null
}
```

## Errors

| Status | When |
|--------|------|
| 401 | Missing `Authorization` header or non-Bearer scheme |

## Frontend notes

1. Call `POST /auth/logout` with the stored `access_token`.
2. Clear **both** `access_token` and `refresh_token` from memory / storage on success.
3. Redirect to the login screen.

**See also:** [refresh.md](refresh.md) · [login.md](login.md)

## Code

- Endpoint: `backend/src/presentation/api/v1/auth/endpoints/logout.py`
- Use-case: `backend/src/application/auth/use_cases/logout.py`
