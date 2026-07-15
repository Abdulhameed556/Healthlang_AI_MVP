# POST /api/v1/auth/password-reset/request

## URL

**Path:** `/api/v1/auth/password-reset/request`

**Full URL:** `<base>/api/v1/auth/password-reset/request`

| Environment | Base URL (`<base>`) | Example full URL |
|-------------|---------------------|------------------|
| Local | `http://localhost:8000` | `http://localhost:8000/api/v1/auth/password-reset/request` |
| Staging | `https://api-staging.example.com` | `https://api-staging.example.com/api/v1/auth/password-reset/request` |
| Production | `https://api.example.com` | `https://api.example.com/api/v1/auth/password-reset/request` |

## Summary

Request a password reset email for an **active email/password** account. The response is
always **200** with a generic message so callers cannot tell whether the email exists
(email enumeration protection).

When a matching account exists, the backend creates a `password_resets` row (bcrypt-hashed
token), expires any older pending resets for that user, and sends an email with a link to
the product SPA.

## Auth

- Required: **no**
- Bearer JWT: not used

## Eligibility

A reset email is sent only when **all** of the following are true:

| Rule | Detail |
|------|--------|
| Account status | `active` |
| Auth method | `email_password` (not Google OAuth–only) |
| Email | Normalized to lowercase |

If the same email has memberships in multiple organizations, the backend picks the active
email/password row with the most recent `updated_at`.

Google OAuth–only users and unknown emails receive the same generic success response; no
email is sent.

## Request

- Content-Type: `application/json`

```json
{
  "email": "user@acme.com"
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `email` | yes | Valid email; trimmed and lowercased server-side |

## Response

### 200 OK

```json
{
  "message": "Password reset request accepted",
  "status_code": 200,
  "error": false,
  "data": {
    "message": "If an account exists for this email, a password reset link has been sent.",
    "reset_link": null
  }
}
```

| Field | Description |
|-------|-------------|
| `data.message` | Generic success text (same whether or not the account exists) |
| `data.reset_link` | **Development only:** when outbound email is disabled, contains the SPA reset URL for local testing. `null` in production after the email is sent. |

### Reset link format (email / dev `reset_link`)

The product SPA receives users at:

```
{PRODUCT_APP_BASE_URL}/auth/reset-password?email={email}&token={token}
```

Example:

```
https://app.example.com/auth/reset-password?email=user%40acme.com&token=url-safe-token
```

Parse `email` and `token` from the query string, then call
[password-reset-complete.md](password-reset-complete.md) with the new password.

Token TTL: **`PASSWORD_RESET_EXPIRE_HOURS`** (default **1 hour**).

### Error responses

| Status | When | Sample `message` |
|--------|------|------------------|
| 422 | Invalid or missing email | `Validation failed` |
| 503 | Database unavailable | `Database temporarily unavailable. Please retry.` |

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `PRODUCT_APP_BASE_URL` | `http://localhost:3000` | Base URL embedded in reset links |
| `PASSWORD_RESET_EXPIRE_HOURS` | `1` | Reset token lifetime |
| `SEND_PASSWORD_RESET_EMAIL_IN_DEV` | `false` | When `APP_ENV=development`, set `true` to send real emails; otherwise links are logged and returned in `data.reset_link` |

## Frontend notes

- Show the same success UI for every email submission (do not reveal whether the account exists).
- **Forgot-password page:** POST this endpoint with the user's email.
- **Reset page:** read `email` + `token` from the URL query, collect new password, call [password-reset-complete.md](password-reset-complete.md).
- In local dev, read `data.reset_link` from the API response if email is not configured.

## Related

- [password-reset-complete.md](password-reset-complete.md) — set new password with token
- [login.md](login.md) — sign in after reset
- Code: `backend/src/presentation/api/v1/auth/endpoints/password_reset.py`
- Use-case: `backend/src/application/auth/use_cases/request_password_reset.py`
