# POST /api/v1/integrations/freshchat/webhook/{webhook_secret}

## URL

**Path:** `/api/v1/integrations/freshchat/webhook/{webhook_secret}`

**Full URL:** `<base>/api/v1/integrations/freshchat/webhook/{webhook_secret}`

| Environment | Base URL (`<base>`) | Example full URL |
|-------------|---------------------|------------------|
| Local (tunnel) | `https://<your-ngrok>.ngrok-free.dev` | `https://<your-ngrok>.ngrok-free.dev/api/v1/integrations/freshchat/webhook/x7Qd…` |
| Staging | `https://api-staging.example.com` | `https://api-staging.example.com/api/v1/integrations/freshchat/webhook/x7Qd…` |
| Production | `https://api.example.com` | `https://api.example.com/api/v1/integrations/freshchat/webhook/x7Qd…` |

> This is **not** called by your frontend. **Freshchat** posts to it. The exact
> URL (with the secret) is returned as `webhook_url` from
> [connect](connect.md) / [get-settings](get-settings.md) — paste it into
> Freshchat's webhook settings.

## Summary

Receives Freshchat webhook events. The `{webhook_secret}` in the path identifies
the org/integration; the `X-Freshchat-Signature` header is verified with that
integration's stored RSA public key. An accepted **customer** `message_create` on
a **routed channel** is enqueued for the AI bot (in-process). Everything else is
acknowledged and ignored.

## Auth

- Required: no JWT (public endpoint — Freshchat calls it directly).
- Authenticated instead by:
  1. **URL secret** — `{webhook_secret}` must match a known integration.
  2. **Signature** — `X-Freshchat-Signature` (base64 `SHA256withRSA`) verified
     against the raw body using the integration's stored public key. If no key is
     stored, `signature_valid` is reported as `null` (not enforced).

## Request

- Sent by Freshchat. Content-Type: application/json.
- Header: `X-Freshchat-Signature: <base64 signature of the raw body>`.
- Body: a Freshchat event (e.g. `message_create`) — shape is defined by Freshchat.

## Response (no envelope)

Unlike the JWT routes, the webhook returns a **bare JSON status object** (no
`message`/`status_code`/`error`/`data` envelope) and **always responds `200 OK`**
so Freshchat does not retry. The body explains what happened.

### Accepted (enqueued for the bot)

```json
{ "status": "received", "signature_valid": true, "queued": true }
```

### Acknowledged but not processed

| Body | Meaning |
|------|---------|
| `{ "status": "ignored", "reason": "unknown_secret" }` | Secret didn't match any integration (dropped quietly). |
| `{ "status": "ok", "reason": "handoff_released" }` | A resolve/reopen event cleared the live-support mute. |
| `{ "status": "ignored", "reason": "<classify reason>" }` | Not a customer `message_create` (bot echo, agent reply, private note, non-message event). |
| `{ "status": "ignored", "reason": "duplicate" }` | Redelivered message id already processed. |
| `{ "status": "ignored", "reason": "handed_off" }` | A human currently owns the conversation; bot stays quiet. |
| `{ "status": "received", "signature_valid": ..., "queued": false, "reason": "channel_not_configured" }` | Inbound channel isn't in this org's `channel_routing`. |
| `{ "status": "received", "signature_valid": ..., "queued": false, "reason": "no_conversation" }` | Message lacked a `conversation_id`. |
| `{ "status": "received", "signature_valid": ..., "queued": false, "reason": "enqueue_failed" }` | Broker hiccup; logged, not retried. |

`signature_valid` is `true`/`false` when a public key is configured, or `null`
when verification isn't configured.

## Behavior notes

- **Always 200.** Failures are recorded in logs, never surfaced as non-200 (which
  would make Freshchat retry).
- **Routing key** is `channel_id`; only channels present in `channel_routing` are
  answered, and by their mapped AI agent.
- **Idempotent** by Freshchat `message_id` (Redis claim) so the bot never answers
  a redelivered message twice.
- **Handoff:** when transferred to live support the conversation is muted; a
  configured resolve/reopen action (`FRESHCHAT_HANDOFF_RELEASE_ACTIONS`) clears it.

## Setup checklist

1. Connect Freshchat → copy `webhook_url`.
2. In Freshchat webhook settings, paste the URL and (recommended) configure the
   RSA public key; store it via `webhook_public_key` on [connect](connect.md) /
   [update-settings](update-settings.md) so signatures are enforced.
3. Send a test message from a routed channel and confirm a `queued: true` log line.

## Related

- [connect.md](connect.md) / [get-settings.md](get-settings.md) — where `webhook_url` comes from
- [../../../../architecture/freshchat-integration.md](../../../../architecture/freshchat-integration.md) — full inbound flow
