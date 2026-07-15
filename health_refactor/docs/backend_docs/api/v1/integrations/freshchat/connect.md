# POST /api/v1/integrations/freshchat/connect

## URL

**Path:** `/api/v1/integrations/freshchat/connect`

**Full URL:** `<base>/api/v1/integrations/freshchat/connect`

| Environment | Base URL (`<base>`) | Example full URL |
|-------------|---------------------|------------------|
| Local | `http://localhost:8000` | `http://localhost:8000/api/v1/integrations/freshchat/connect` |
| Staging | `https://api-staging.example.com` | `https://api-staging.example.com/api/v1/integrations/freshchat/connect` |
| Production | `https://api.example.com` | `https://api.example.com/api/v1/integrations/freshchat/connect` |

## Summary

Validates the Freshchat credentials + selected sender agent and stores (or
reconnects) the org's Freshchat integration with its per-channel routing. Called
once when an org first wires up Freshchat (after [resources.md](resources.md)
populates the form).

## Auth

- Required: yes
- Header: `Authorization: Bearer <access_token>` (optional `X-Organization-Id`)
- Minimum role: `super_admin` or `admin`

## Request

- Content-Type: application/json

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `account_url` | string | yes | e.g. `https://acme.freshchat.com` |
| `api_token` | string | yes | Freshchat API token (Bearer). Stored encrypted; validated against the account. |
| `freshchat_agent_id` | string | yes | Freshchat agent the bot posts replies as. |
| `live_support_group_id` | string \| null | no | Freshchat group for human handoff. |
| `channel_routing` | array | no | Per-channel routing entries (below). |
| `channel_routing[].channel_id` | string | yes | Freshchat channel UUID (the routing key; matches webhook `channel_id`). |
| `channel_routing[].agent_id` | UUID | yes | Platform AI agent that answers on this channel. |
| `channel_routing[].freshchat_channel_id` | string \| null | no | Numeric Freshchat channel id, for reference only. |
| `webhook_public_key` | string \| null | no | Freshchat webhook RSA public key (PEM). Stored encrypted; reused on reconnect when omitted. |

**Sample body:**

```json
{
  "account_url": "https://acme.freshchat.com",
  "api_token": "eyJraWQiOiJjdXN0b20tb2F1dGgta2V5aWQ...",
  "freshchat_agent_id": "1074a906-95b5-44d3-9d68-de15d96ba4e5",
  "live_support_group_id": "60f78839-f714-45d2-b75c-dd1ef19f5e9d",
  "channel_routing": [
    {
      "channel_id": "3518515b-d192-4d9e-8b0e-cc4c8260c0a3",
      "agent_id": "b94f4bf0-d789-4d74-844c-1ff15530114e",
      "freshchat_channel_id": "818162"
    }
  ],
  "webhook_public_key": "-----BEGIN RSA PUBLIC KEY-----\nMIIBIjANBgkq...\n-----END RSA PUBLIC KEY-----"
}
```

## Response envelope (backend product API)

### 201 Created

`data` is the [shared connection shape](README.md#shared-connection-shape-data).
Use `data.webhook_url` — paste it into Freshchat's webhook settings.

```json
{
  "message": "Freshchat connected successfully",
  "status_code": 201,
  "error": false,
  "data": {
    "integration_id": "9b1f...",
    "provider": "freshchat",
    "status": "active",
    "account_url": "https://acme.freshchat.com",
    "account_domain": "acme.freshchat.com",
    "freshchat_agent_id": "1074a906-95b5-44d3-9d68-de15d96ba4e5",
    "live_support_group_id": "60f78839-f714-45d2-b75c-dd1ef19f5e9d",
    "channel_routing": [
      {
        "channel_id": "3518515b-d192-4d9e-8b0e-cc4c8260c0a3",
        "agent_id": "b94f4bf0-d789-4d74-844c-1ff15530114e",
        "freshchat_channel_id": "818162",
        "channel_name": null
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
| 400 | Freshchat rejected the API token (401 from Freshchat), or selected agent not found in the account | `{ "message": "Freshchat rejected the API token (401)", "status_code": 400, "error": true, "data": null }` |
| 401 | Missing/invalid session JWT | `{ "message": "...", "status_code": 401, "error": true, "data": null }` |
| 403 | Caller is not `super_admin`/`admin` | `{ "message": "...", "status_code": 403, "error": true, "data": null }` |
| 422 | Schema validation (missing `account_url`/`api_token`/`freshchat_agent_id`, bad `agent_id` UUID) | `data` may contain `{ "errors": [...] }` |
| 502 | Freshchat API unreachable / upstream error | `{ "message": "...", "status_code": 502, "error": true, "data": null }` |

## Frontend notes

- Connecting **validates** the token (lists agents) and that `freshchat_agent_id`
  exists in the account — a wrong token or agent fails fast.
- After success, surface `data.webhook_url` prominently with a copy button; the
  org must paste it into Freshchat for inbound events to arrive.
- Calling connect again **reconnects/overwrites** the org's Freshchat config.
  Omit `webhook_public_key` to keep the previously stored one.
- The API token and public key are never returned; rely on `has_api_token` /
  `has_webhook_public_key` to show "configured" state.

## Related

- [resources.md](resources.md) — populate the connect form's dropdowns
- [get-settings.md](get-settings.md) · [update-settings.md](update-settings.md)
- [webhook.md](webhook.md) — where the `webhook_url` points
