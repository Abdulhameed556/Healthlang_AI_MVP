# POST /api/v1/invitations/{token}/decline

## URL

**Path:** `/api/v1/invitations/{token}/decline`

**Full URL:** `<base>/api/v1/invitations/{token}/decline`

| Environment | Base URL (`<base>`) | Example full URL |
|-------------|---------------------|------------------|
| Local | `http://localhost:8000` | `http://localhost:8000/api/v1/invitations/abc123/decline` |
| Staging | `https://api-staging.example.com` | `https://api-staging.example.com/api/v1/invitations/abc123/decline` |
| Production | `https://api.example.com` | `https://api.example.com/api/v1/invitations/abc123/decline` |

Replace `{token}` with the invitation token from the invite link.

## Summary

Declines a pending invitation. Sets invitation status to `declined` and user status to
`invitation_declined` when applicable. Idempotent if already declined.

## Auth

- Required: no

## Request

- No body
- Path parameter: `token` — invitation token

## Response

### 200 OK

```json
{
  "message": "Invitation declined",
  "status_code": 200,
  "error": false,
  "data": {
    "invitation_id": "550e8400-e29b-41d4-a716-446655440002",
    "email": "admin@acme.com"
  }
}
```

### Error responses

| Status | When | Sample `message` |
|--------|------|------------------|
| 404 | Unknown token | `Invitation not found` |
| 422 | Invitation not pending (e.g. already accepted) | `Invitation is accepted` |

## Frontend notes

- Call from the invite landing page “Decline” action.
- After decline, login / accept flows should not succeed until Admin re-provisions the user.
- Already-declined invites return **200** with the same shape (safe to retry).

## Related

- [../auth/login.md](../auth/login.md) — accept via email/password
- [../auth/google-login.md](../auth/google-login.md) — accept via Google
- Code: `backend/src/presentation/api/v1/invitations/endpoints/decline_invitation.py`
