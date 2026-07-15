# POST /api/v1/integrations/freshchat/resources

## URL

**Path:** `/api/v1/integrations/freshchat/resources`

**Full URL:** `<base>/api/v1/integrations/freshchat/resources`

| Environment | Base URL (`<base>`) | Example full URL |
|-------------|---------------------|------------------|
| Local | `http://localhost:8000` | `http://localhost:8000/api/v1/integrations/freshchat/resources` |
| Staging | `https://api-staging.example.com` | `https://api-staging.example.com/api/v1/integrations/freshchat/resources` |
| Production | `https://api.example.com` | `https://api.example.com/api/v1/integrations/freshchat/resources` |

## Summary

Fetches the Freshchat account's **channels**, **groups**, and **agents** for the
given credentials so the connect form can populate its dropdowns. Read-only —
persists nothing. POST (not GET) because the credentials travel in the body.

## Auth

- Required: yes
- Header: `Authorization: Bearer <access_token>` (optional `X-Organization-Id`)
- Minimum role: `super_admin` or `admin`

## Request

- Content-Type: application/json

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `account_url` | string | yes | e.g. `https://acme.freshchat.com` |
| `api_token` | string | yes | Freshchat API token (Bearer). Not stored by this endpoint. |

**Sample body:**

```json
{
  "account_url": "https://acme.freshchat.com",
  "api_token": "eyJraWQiOiJjdXN0b20tb2F1dGgta2V5aWQ..."
}
```

## Response envelope (backend product API)

### 200 OK

```json
{
  "message": "Freshchat resources retrieved successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "channels": [
      {
        "id": "3518515b-d192-4d9e-8b0e-cc4c8260c0a3",
        "name": "WHATSAPP_+15559677139",
        "enabled": true,
        "public": false
      },
      {
        "id": "5dd35c34-45d5-43fb-a598-f629a710be42",
        "name": "Afriex Support",
        "enabled": true,
        "public": true
      }
    ],
    "groups": [
      { "id": "60f78839-f714-45d2-b75c-dd1ef19f5e9d", "name": "Live Support", "description": "" }
    ],
    "agents": [
      { "id": "1074a906-95b5-44d3-9d68-de15d96ba4e5", "email": "bot@acme.com", "name": "Ada Bot" }
    ]
  }
}
```

| Field | Notes |
|-------|-------|
| `channels[].id` | The `channel_id` to use in `channel_routing`. |
| `channels[].public` | `true` = web/mobile widget topic; `false` = external channel (WhatsApp/Instagram/Messenger). |
| `groups[].id` | Candidate for `live_support_group_id` (handoff). |
| `agents[].id` | Candidate for `freshchat_agent_id` (bot sender). |

### Error responses

| Status | When | Sample body |
|--------|------|-------------|
| 400 | Missing `account_url`/`api_token`, or Freshchat rejected the token (401 upstream) | `{ "message": "Freshchat rejected the API token (401)", "status_code": 400, "error": true, "data": null }` |
| 401 | Missing/invalid session JWT | `{ "message": "...", "status_code": 401, "error": true, "data": null }` |
| 403 | Caller is not `super_admin`/`admin` | `{ "message": "...", "status_code": 403, "error": true, "data": null }` |
| 422 | Schema validation | `data` may contain `{ "errors": [...] }` |
| 502 | Freshchat API unreachable / upstream error | `{ "message": "...", "status_code": 502, "error": true, "data": null }` |

## Frontend notes

- Call this first in the connect wizard, then map selections into [connect](connect.md):
  - a channel `id` → `channel_routing[].channel_id`
  - a group `id` → `live_support_group_id`
  - an agent `id` → `freshchat_agent_id`
- This is also the implicit **credential check**: a bad token fails here before
  the user fills the rest of the form.
- Reaching Freshchat live, this is slower than a DB read — show a loading state.

## Related

- [connect.md](connect.md) — where these selections are submitted
