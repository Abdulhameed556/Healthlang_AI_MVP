# Freshchat Integration API (`/api/v1/integrations/freshchat`)

Connect an organization's Freshchat account so the AI bot answers conversations
(WhatsApp, Instagram, Messenger, web/mobile widgets bridged through Freshchat) and
hands off to live support when needed.

Most routes are JWT-protected and organization-scoped. Send
`Authorization: Bearer <access_token>` on every call; obtain the token from
[login](../../auth/login.md) or [Google login](../../auth/google-login.md). For
multi-org users, optionally add `X-Organization-Id` — see
[organization context](../../auth/organization-context.md).

The **webhook** route is the one exception: it is public (Freshchat calls it
directly) and is authenticated by a secret embedded in its URL plus an RSA
signature, not by a JWT.

| Doc | Method | Path | Who can call |
|-----|--------|------|--------------|
| [resources.md](resources.md) | POST | `/api/v1/integrations/freshchat/resources` | `super_admin`, `admin` |
| [connect.md](connect.md) | POST | `/api/v1/integrations/freshchat/connect` | `super_admin`, `admin` |
| [get-settings.md](get-settings.md) | GET | `/api/v1/integrations/freshchat/settings` | All roles |
| [update-settings.md](update-settings.md) | PATCH | `/api/v1/integrations/freshchat/settings` | `super_admin`, `admin` |
| [webhook.md](webhook.md) | POST | `/api/v1/integrations/freshchat/webhook/{webhook_secret}` | Public (Freshchat) |
| [delete-integration.md](../delete-integration.md) | DELETE | `/api/v1/integrations/{integration_id}` | `super_admin`, `admin` |

## Response envelope

All JWT routes return the standard envelope:

```json
{
  "message": "…",
  "status_code": 200,
  "error": false,
  "data": { }
}
```

On failure, `error` is `true` and `data` is typically `null`. The **webhook**
route is the exception — it returns a small bare JSON status object (no envelope)
and always responds `200` so Freshchat does not retry. See [webhook.md](webhook.md).

## How a connection is set up (UI flow)

1. **List resources** ([resources.md](resources.md)) with the account URL + API
   token → returns the account's **channels**, **groups**, and **agents** so the
   form can populate dropdowns. Nothing is stored.
2. **Connect** ([connect.md](connect.md)) with the chosen sender agent, the
   per-channel routing (which platform AI agent answers on which Freshchat
   channel), an optional handoff group, and an optional webhook public key.
3. Paste the returned **`webhook_url`** into Freshchat's webhook settings.
4. **Read / update** settings anytime ([get-settings.md](get-settings.md),
   [update-settings.md](update-settings.md)) without re-entering credentials.

## Key concepts

### `channel_id` vs `freshchat_channel_id`

| Field | Type | Role |
|-------|------|------|
| `channel_id` | UUID string | **The routing key.** Matches the `channel_id` Freshchat sends on inbound webhook events. This is what decides whether (and by which AI agent) a message is answered. |
| `freshchat_channel_id` | numeric string \| null | Optional human reference (the numeric id shown in some Freshchat screens). Stored only for convenience; not used for routing. |

A Freshchat "channel" is a **topic**. Public (`public: true`) topics are the
web/mobile widget surfaces; WhatsApp/Instagram/Messenger appear as
`public: false` channels. All have a `channel_id`.

### `freshchat_agent_id` (the bot's sender identity)

The Freshchat agent the bot **posts replies as**. Chosen from the account's
agents list returned by [resources.md](resources.md). Omni accounts block
creating agents via API, so an existing agent is selected rather than
auto-created.

### `live_support_group_id` (handoff)

The Freshchat group a conversation is assigned to when the bot transfers to a
human. Assignment uses status **`new`** by default (`FRESHCHAT_HANDOFF_STATUS`) so
the group queue (IntelliAssign) can pick it up — not `assigned`, which requires a
specific agent id. While handed off, the bot stays quiet until Freshchat signals
the conversation was resolved/reopened. A handoff also always opens a ticket so
the human inherits a record.

### Credentials & secrets

| Value | Stored | Returned by API |
|-------|--------|-----------------|
| `api_token` | Encrypted at rest | Never. `has_api_token` indicates presence only. |
| `webhook_public_key` | Encrypted at rest | Never. `has_webhook_public_key` indicates presence only. |
| `webhook_secret` | Plain (it *is* the URL identifier) | Yes, plus the full `webhook_url`. |

## Shared connection shape (`data`)

`connect`, `get settings`, and `update settings` all return the same object:

```json
{
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
```

| Field | Notes |
|-------|-------|
| `freshchat_agent_name`, `live_support_group_name`, `channel_routing[].channel_name` | Resolved from Freshchat **best-effort** on `GET /settings`; may be `null` if Freshchat is unreachable. On `connect`/`update` they may be `null`. |
| `agent_id` (in `channel_routing`) | A **platform** AI agent UUID (not a Freshchat id). |
| `webhook_url` | Built from `API_PUBLIC_BASE_URL`; paste into Freshchat. |

## How it works (architecture)

For the end-to-end design — webhook verification, routing, dedup, the AI bot
loop, mid-conversation ticketing, and live-support handoff — see
[../../../../architecture/freshchat-integration.md](../../../../architecture/freshchat-integration.md).

**Related:** [../../../endpoints.md](../../../endpoints.md) (all routes) · [../../auth/login.md](../../auth/login.md)
