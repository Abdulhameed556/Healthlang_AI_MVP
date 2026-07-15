# POST /api/v1/auth/password-reset/complete

## URL

**Path:** `/api/v1/auth/password-reset/complete`

**Full URL:** `<base>/api/v1/auth/password-reset/complete`

| Environment | Base URL (`<base>`) | Example full URL |
|-------------|---------------------|------------------|
| Local | `http://localhost:8000` | `http://localhost:8000/api/v1/auth/password-reset/complete` |
| Staging | `https://api-staging.example.com` | `https://api-staging.example.com/api/v1/auth/password-reset/complete` |
| Production | `https://api.example.com` | `https://api.example.com/api/v1/auth/password-reset/complete` |

## Summary

Set a new password using the **`email`** and **`token`** from the reset link sent after
[password-reset-request.md](password-reset-request.md). On success, all existing sessions
for that user are invalidated; the user must log in again with the new password.

## Auth

- Required: **no**
- Bearer JWT: not used

## Request

- Content-Type: `application/json`

```json
{
  "email": "user@acme.com",
  "token": "url-safe-token-from-reset-link",
  "new_password": "NewSecurePass123"
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `email` | yes | Must match `email` query param from the reset link; trimmed and lowercased |
| `token` | yes | Plain token from the reset link (not the bcrypt hash stored in the DB) |
| `new_password` | yes | Min 8 characters; stored as bcrypt hash |

## Response

### 200 OK

```json
{
  "message": "Password reset successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "message": "Password reset successfully"
  }
}
```

After success:

1. The user's `password_hash` is updated.
2. The matching `password_resets` row is marked `used`.
3. All `user_sessions` for that user are invalidated.

Redirect the user to login with [login.md](login.md).

### Error responses

| Status | When | Sample `message` |
|--------|------|------------------|
| 401 | Wrong token, expired token, unknown email, or already-used link | `Invalid or expired password reset link` |
| 422 | Validation (short password, missing fields) | `Validation failed` |
| 503 | Database unavailable | `Database temporarily unavailable. Please retry.` |

The API returns the same **401** message for invalid, expired, and reused tokens to avoid
leaking which case occurred.

## Multi-organization note

If the same email exists in multiple organizations, the backend checks pending reset rows
across all user rows for that email and applies the password change to the membership row
that matches the valid token.

## Frontend notes

- **Reset page flow:**
  1. Parse `email` and `token` from `{PRODUCT_APP_BASE_URL}/auth/reset-password?...`.
  2. User enters new password (and confirm field in UI only).
  3. POST this endpoint with `email`, `token`, `new_password`.
  4. On **200**, redirect to login with a success message.
  5. On **401**, show “link expired or invalid” and offer to request a new reset.
- Do not send the reset token as a Bearer header; it belongs in the JSON body only.

## Related

- [password-reset-request.md](password-reset-request.md) — request reset email
- [login.md](login.md) — sign in with new password
- Code: `backend/src/presentation/api/v1/auth/endpoints/password_reset.py`
- Use-case: `backend/src/application/auth/use_cases/complete_password_reset.py`
