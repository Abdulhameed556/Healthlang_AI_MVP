# Freshchat Integration — How It Works

How an organization's Freshchat account is connected and how the AI bot answers
conversations end to end (WhatsApp, Instagram, Messenger, and web/mobile widgets
bridged through Freshchat), including live-agent handoff and mid-conversation
ticketing.

- **API reference:** [../api/v1/integrations/freshchat/README.md](../api/v1/integrations/freshchat/README.md)
- **Related AI design:** [../../ai_docs/architecture/chat-pipeline.md](../../ai_docs/architecture/chat-pipeline.md),
  [../../ai_docs/architecture/session-close-and-ticketing.md](../../ai_docs/architecture/session-close-and-ticketing.md)

## 1. Goal & shape

Freshchat is the **channel hub**: customers message on WhatsApp/IG/Messenger/web,
Freshchat normalizes those into conversations and emits webhooks. We:

1. Let an org connect its Freshchat account and choose **which AI agent answers
   which channel**.
2. Receive Freshchat webhooks, verify them, and run the **AI bot loop** to reply.
3. **Hand off** to a human group when the bot decides to, staying quiet until the
   human is done.
4. **Ticket** issues mid-conversation (and always on handoff) for record-keeping.

The integration reuses the generic `integrations` table and the existing AI chat
pipeline; Freshchat-specific behavior is isolated under `integrations/freshchat/`
folders and a single `ExternalTurnContext` seam in the pipeline.

## 2. Data model

One row in the generic `integrations` table per org (provider `freshchat`):

| Column | Holds |
|--------|-------|
| `credentials_encrypted` | Freshchat API token (encrypted at rest) |
| `webhook_secret` | URL-safe secret embedded in the webhook URL (identifies the integration on inbound calls) |
| `config` (JSONB) | Everything else (below) |

`config` keys (see `application/integrations/freshchat/services.py`):

| Key | Meaning |
|-----|---------|
| `base_url` / `account_domain` | Freshchat account URL + host |
| `freshchat_agent_id` | Bot's sender identity (the agent replies are posted as) |
| `live_support_group_id` | Group for human handoff |
| `channel_routing` | List of `{ channel_id, agent_id, freshchat_channel_id }` — which **platform AI agent** answers which **Freshchat channel** |
| `webhook_public_key_encrypted` | Freshchat's RSA public key (PEM), encrypted, for signature verification |

`channel_id` (UUID) is the **routing key** and matches what Freshchat sends on
webhooks. `freshchat_channel_id` (numeric) is reference-only.

## 3. Connection setup

1. **`POST /resources`** — with account URL + token, fetch the account's
   channels, groups, and agents (also an implicit credential check). Nothing is
   stored.
2. **`POST /connect`** — validates the token (lists agents) and that the chosen
   `freshchat_agent_id` exists, then stores the integration + routing and returns
   a `webhook_url` (built from `API_PUBLIC_BASE_URL` + `webhook_secret`).
3. Paste `webhook_url` into Freshchat; store Freshchat's RSA public key via
   `webhook_public_key`.
4. **`GET /settings`** / **`PATCH /settings`** — read (with resolved names) or
   update config without re-entering credentials.

> Omni accounts block `POST /agents` (403), so the bot uses an **existing**
> Freshchat agent as its sender rather than auto-creating one.

## 4. Inbound webhook flow

`POST /webhook/{webhook_secret}` (`presentation/.../freshchat/endpoints/webhook.py`)
is public and **always returns 200** so Freshchat never retries. Steps:

1. **Resolve integration** from the URL secret (`get_by_webhook_secret`). Unknown
   → `{"status":"ignored","reason":"unknown_secret"}`.
2. **Verify signature** — `X-Freshchat-Signature` (base64 `SHA256withRSA`) against
   the **raw** body using the integration's stored public key
   (`infrastructure/.../webhook_security.py`). No key stored → `signature_valid: null`.
3. **Handoff release** — if the event is a configured resolve/reopen action
   (`FRESHCHAT_HANDOFF_RELEASE_ACTIONS`), clear the mute and return.
4. **Classify** (`application/.../freshchat/inbound.py`) — only a **customer**
   `message_create` proceeds; bot echoes, agent replies, private notes, and
   non-message events are ignored.
5. **Dedup** by Freshchat `message_id` (Redis `SET NX`,
   `infrastructure/.../freshchat/dedup.py`) — redelivered messages drop.
6. **Handoff check** — if a human owns the conversation, stay quiet
   (`reason: handed_off`).
7. **Route** — map the inbound `channel_id` to a platform `agent_id`. Unconfigured
   channel → `queued: false, reason: channel_not_configured`.
8. **Enqueue** the normalized `FreshchatInboundJob` to the AI worker.

### In-process enqueue (no HTTP hop)

The backend and AI worker run in **one process**, so the webhook hands off via a
direct Dramatiq enqueue (`get_freshchat_enqueuer`), not an internal REST call.
AI imports are lazy so importing the webhook module never configures the broker.

## 5. The AI bot loop (worker)

`ai/src/application/chat/freshchat_inbound.py` → `process_freshchat_inbound`:

1. **Resolve session** — one `ChatSession` per Freshchat `conversation_id`
   (`find_active_by_freshchat_conversation`, else create + link via metadata).
2. **Run the chat pipeline** with `ExternalTurnContext(source="freshchat")`, which
   enables the orchestrator's mid-conversation ticket signal.
3. **Send the reply** back to the conversation as `freshchat_agent_id`
   (`client.send_message`).
4. **Ticket** if the orchestrator signalled one (or always, on handoff — see §6).
5. **Hand off** if the turn's state is `transfer_to_live_support` (see §7).
6. **Resolve in Freshchat** if the turn's state is `end_conversation` — marks the
   Freshchat conversation resolved (`FRESHCHAT_RESOLVE_STATUS`, default `resolved`)
   after the closing reply is sent.

### Synchronous persistence in the worker

Each Dramatiq job runs on its own short-lived event loop. Async persistence would
schedule the DB write as a background task the loop kills on return — leaving the
Redis cache (closed) and DB (active) out of sync. So the worker uses
`async_session_persist=False` (`WORKER_CHAT_CONFIG`): the turn is persisted before
the job ends.

### Closed-session recovery

If the resolved session is found closed mid-run (e.g. a transfer on a prior turn
or a close/new-message race), the processor catches `ChatSessionClosedError`,
creates a **fresh** session for the same conversation, and re-runs — instead of
failing and retrying forever.

## 6. Mid-conversation ticketing

The orchestrator emits `ticket_action` (`none` | `create_ticket`) + `ticket_reason`
each turn (`domain/chat_system/v1/types.py`). When it signals a ticket, we open
one **without closing** the conversation (`create_conversation_ticket`), linking
only the as-yet-unticketed logs and stamping a marker on the latest assistant
turn so later turns see it and don't duplicate.

- The ticketing agent's `worth_ticket` is **recorded but does not veto** the
  orchestrator's decision.
- **A live-support handoff always tickets**, overriding `ticket_action: none`, so
  the human inherits a record (falls back to a "transferred to live support"
  reason when the orchestrator gave none).
- On **`end_conversation`**, the orchestrator may set `issue_resolved` (`true` /
  `false` / `null`). When present, it overrides the ticketing agent's resolution
  outcome on the ticket created for that close/handoff.

## 7. Live-support handoff

When a turn's state is `transfer_to_live_support`:

1. **Assign** the conversation to `live_support_group_id` with status `new` (group
   queue for IntelliAssign; `assigned` requires a specific agent id) via
   `client.assign_conversation`.
2. **Mute** the bot for that conversation: `FreshchatHandoffState.mark` sets a
   Redis flag `freshchat:handoff:<integration>:<conversation>` (25h TTL backstop).
3. While muted, inbound customer messages return `reason: handed_off` (bot quiet).
4. **Release** is event-driven: a configured resolve/reopen webhook action clears
   the flag, so the bot resumes the moment the human is done — not on a timer.

If no `live_support_group_id` is configured, the bot does not mute (nothing to
hand off to).

## 8. Session & history model

- **One long-lived `ChatSession` per Freshchat `conversation_id`** (linked via
  session metadata; `freshchat_session.py`, `session_link.py`).
- We **do not** track Freshchat's 24h window ourselves — Freshchat owns that. We
  key off `conversation_id` and our stored history.
- History is mapped to LLM messages with inline **ticket markers**
  (`ai/src/application/chat/history.py`) so the model knows what it already
  ticketed in this thread.

## 9. Configuration (env)

| Setting | Purpose | Default |
|---------|---------|---------|
| `API_PUBLIC_BASE_URL` | Builds the pasteable `webhook_url` | — |
| `FRESHCHAT_WEBHOOK_PUBLIC_KEY` | Fallback public key if none stored per-integration | "" |
| `FRESHCHAT_WEBHOOK_CAPTURE_TO_FILE` | Also write each raw event to a JSON file (debug) | off |
| `FRESHCHAT_HANDOFF_STATUS` | Status sent with `assign_conversation` on handoff | `new` |
| `FRESHCHAT_HANDOFF_RELEASE_ACTIONS` | Webhook actions that clear the handoff mute | `conversation_resolution,conversation_reopen` |
| `FRESHCHAT_RESOLVE_STATUS` | Status sent to resolve the conversation when the bot ends it | `resolved` |

## 10. Observability

- The webhook logs one structured line per event (org, integration, action,
  `signature_valid`, `channel_id`, `channel_configured`, routed agent, ids, text)
  plus the full payload.
- The pipeline logs per-step durations (`step=scenario_routing … duration_ms=`,
  `orchestration`, `persist_turn`, `turn_complete`).
- The worker emits a **green** end-of-turn timing summary
  (`freshchat_timing … total=… resolve=… pipeline=… send=… ticket=… handoff=…
  resolve_conv=…`) via `green()` in `backend/src/core/logging.py` so the slowest
  phase is obvious.

## 11. WhatsApp delivery caveat (out of our control)

Our `send_message` returning `200` means Freshchat **accepted** the reply. Whether
WhatsApp **delivers** it is a separate Meta-side decision (24h customer-care
window, number quality rating, billing/payment method, throttling). Freshchat
surfaces Meta rejections as a generic error (e.g. code **4131** "service provider
error"). These are account/billing/window issues, not bugs in this integration,
and are diagnosed in WhatsApp Manager.

## 12. Key modules

| Concern | Module |
|---------|--------|
| API client (httpx) | `backend/src/infrastructure/integrations/freshchat/client.py` |
| Webhook signature | `backend/src/infrastructure/integrations/freshchat/webhook_security.py` |
| Dedup | `backend/src/infrastructure/integrations/freshchat/dedup.py` |
| Channel name cache (Redis, 1h) | `backend/src/infrastructure/integrations/freshchat/channel_cache.py` |
| Handoff state (Redis) | `backend/src/infrastructure/integrations/freshchat/handoff.py` |
| Inbound classify/extract | `backend/src/application/integrations/freshchat/inbound.py` |
| Services / config mapping | `backend/src/application/integrations/freshchat/services.py` |
| Use cases | `backend/src/application/integrations/freshchat/use_cases/` |
| Endpoints | `backend/src/presentation/api/v1/integrations/freshchat/endpoints/` |
| Bot loop | `ai/src/application/chat/freshchat_inbound.py` |
| Session resolve | `ai/src/application/chat/freshchat_session.py` |
| Mid-convo ticket | `ai/src/application/chat/conversation_ticket.py` |
| Worker task | `ai/src/infrastructure/workers/tasks/freshchat_inbound.py` |

## 13. Testing

Each meaningful module is mirrored by a unit test under `tests/` (client, webhook
security, dedup, handoff, inbound classify, services, use cases, endpoints, the
bot loop, session resolve, mid-conversation ticketing, and the worker task).
