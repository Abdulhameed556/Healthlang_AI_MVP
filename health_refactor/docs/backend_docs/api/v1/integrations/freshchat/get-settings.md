# GET /api/v1/integrations/freshchat/settings

## URL

**Path:** `/api/v1/integrations/freshchat/settings`

**Full URL:** `<base>/api/v1/integrations/freshchat/settings`

| Environment | Base URL (`<base>`) | Example full URL |
|-------------|---------------------|------------------|
| Local | `http://localhost:8000` | `http://localhost:8000/api/v1/integrations/freshchat/settings` |
| Staging | `https://api-staging.example.com` | `https://api-staging.example.com/api/v1/integrations/freshchat/settings` |
| Production | `https://api.example.com` | `https://api.example.com/api/v1/integrations/freshchat/settings` |

## Summary

Returns the org's saved Freshchat configuration for pre-filling the settings
screen, including human-readable names for the sender agent, routed channels, and
handoff group.

## Auth

- Required: yes
- Header: `Authorization: Bearer <access_token>` (optional `X-Organization-Id`)
- Minimum role: all roles (read)

## Request

- No body. No query params.

## Response envelope (backend product API)

### 200 OK

`data` is the [shared connection shape](README.md#shared-connection-shape-data).
Names (`freshchat_agent_name`, `live_support_group_name`,
`channel_routing[].channel_name`) are resolved from Freshchat **best-effort** and
may be `null` if Freshchat is unreachable or the resource was removed.

```json
{
  "message": "Freshchat settings retrieved",
  "status_code": 200,
  "error": false,
  "data": {
    "integration_id": "9b1f...",
    "provider": "freshchat",
    "status": "active",
    "account_url": "https://acme.freshchat.com",
    "account_domain": "acme.freshchat.com",
    "freshchat_agent_id": "1074a906-95b5-44d3-9d68-de15d96ba4e5",
    "freshchat_agent_name": "Ada Bot",
    "live_support_group_id": "60f78839-f714-45d2-b75c-dd1ef19f5e9d",
    "live_support_group_name": "Live Support",
    "channel_routing": [
      {
        "channel_id": "3518515b-d192-4d9e-8b0e-cc4c8260c0a3",
        "agent_id": "b94f4bf0-d789-4d74-844c-1ff15530114e",
        "freshchat_channel_id": "818162",
        "channel_name": "WHATSAPP_+15559677139"
      }
    ],
    "has_api_token": true,
    "has_webhook_public_key": true,
    "webhook_secret": "x7Qd…urlsafe…",
    "webhook_url": "https://api.example.com/api/v1/integrations/freshchat/webhook/x7Qd…urlsafe…",
    "created_at": "2026-06-25T09:00:00Z",
    "updated_at": "2026-06-25T09:00:00Z"
  }
}
```

### Error responses

| Status | When | Sample body |
|--------|------|-------------|
| 401 | Missing/invalid session JWT | `{ "message": "...", "status_code": 401, "error": true, "data": null }` |
| 404 | Freshchat is not connected for this org | `{ "message": "Freshchat is not connected", "status_code": 404, "error": true, "data": null }` |

## Frontend notes

- Show names (`*_name`) when present; fall back to the id when `null`.
- This call hits Freshchat to resolve names, so it is slightly slower than a pure
  DB read; a brief spinner is appropriate. Ids always return even when names don't.
- The API token and webhook public key are never returned — use `has_api_token`
  and `has_webhook_public_key` for "configured" badges.
- Re-display `webhook_url` here so users can re-copy it into Freshchat.

## Related

- [update-settings.md](update-settings.md) — change config without re-entering credentials
- [connect.md](connect.md)
