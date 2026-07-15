# Admin Login (two-step: password → OTP)

Admin login is a **two-step** flow. Step 1 validates the password and emails a
6-digit OTP; step 2 exchanges the OTP for an access token. Sessions last
**60 minutes** with **no refresh token**.

---

## Step 1 — POST `/admin/api/v1/auth/login/initiate`

**Full URL (local):** `http://localhost:8000/admin/api/v1/auth/login/initiate`

### Summary
Validates the admin's email + password. On success, emails a 6-digit OTP.
Always returns **200** with a generic message (so it can't be used to discover
which emails exist).

### Auth
None (public).

### Request
```json
{
  "email": "admin@platform.com",
  "password": "S3cure-Pass!"
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `email` | yes | Case-insensitive |
| `password` | yes | Min 1 char |

### Response (200)
```json
{ "message": "OTP sent to your email" }
```

### Errors
| Status | When |
|--------|------|
| 401 | Invalid email or password |
| 422 | Missing/invalid fields |
| 423 | Account locked after too many failed attempts |

---

## Step 2 — POST `/admin/api/v1/auth/login/verify`

**Full URL (local):** `http://localhost:8000/admin/api/v1/auth/login/verify`

### Summary
Exchanges the email + OTP for an admin access token.

### Auth
None (public).

### Request
```json
{
  "email": "admin@platform.com",
  "otp": "482913"
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `email` | yes | Same email as step 1 |
| `otp` | yes | Exactly 6 digits |

### Response (200)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "must_change_password": false
}
```

| Field | Description |
|-------|-------------|
| `access_token` | Admin JWT; send as `Authorization: Bearer <token>` |
| `token_type` | Always `bearer` |
| `must_change_password` | Advisory flag; not enforced yet |

### Errors
| Status | When |
|--------|------|
| 401 | Invalid or expired OTP |
| 422 | Missing/invalid fields |

---

## Frontend flow
1. Collect email + password → `POST /login/initiate`.
2. Show an OTP entry screen.
3. Collect the 6-digit OTP → `POST /login/verify`.
4. Store `access_token`; attach it as `Authorization: Bearer <token>` on every call.
5. On logout, call [logout.md](logout.md).

## Code
- Endpoints: `admin/src/presentation/api/v1/auth/endpoints/login.py`
- Use-case: `admin/src/application/auth/use_cases/login_with_email.py`
