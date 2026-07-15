# Tickets API (`/api/v1/tickets`)

JWT-protected, organization-scoped routes for listing, searching, viewing, and
manually creating support tickets (chat and voice).

Send `Authorization: Bearer <access_token>` on every call. Obtain the token from
[login](../auth/login.md) or [Google login](../auth/google-login.md). For multi-org
users, optionally add `X-Organization-Id` — see
[organization context](../auth/organization-context.md).

| Doc | Method | Path | Who can call |
|-----|--------|------|--------------|
| [list-tickets.md](list-tickets.md) | GET | `/api/v1/tickets/` | All roles |
| [get-ticket.md](get-ticket.md) | GET | `/api/v1/tickets/{ticket_id}` | All roles |
| [create-ticket.md](create-ticket.md) | POST | `/api/v1/tickets/` | All roles |

## How tickets are created

Most tickets are created automatically: when a chat/voice session closes, the
post-close pipeline summarises the conversation and — when it is ticket-worthy —
persists a ticket linked to that session. [create-ticket.md](create-ticket.md) is
for **manual** tickets that are not tied to a session.

Every ticket gets a unique, human-readable `reference` like `TICK-62YHW`
(generated server-side; Crockford base32, prefix `TICK-`).

## Standard envelope

All endpoints return:

```json
{
  "message": "…",
  "status_code": 200,
  "error": false,
  "data": { }
}
```

On failure, `error` is `true` and `data` is typically `null`.

## Categorical fields

### `status`

Lifecycle state of the ticket.

| Value | Description |
|-------|-------------|
| `open` | Active / unresolved |
| `resolved` | Closed successfully |
| `transferred` | Handed off to live/human support |
| `failed` | Could not be handled |
| `unknown` | Status not determined |

### `interface_type`

Channel the ticket originated from.

| Value | Description |
|-------|-------------|
| `chat` | Text-based session (agent number is `null`) |
| `voice` | Voice session |

### `resolution`

Optional qualifier describing **how** a ticket ended. Distinct from `status`
(lifecycle state) — a ticket can be `status: transferred` with
`resolution: transferred`, or `status: open` with `resolution: N/A`.

| Value | Description |
|-------|-------------|
| `resolved` | The customer's issue was solved |
| `transferred` | Escalated to a human/live agent |
| `abandoned` | Customer dropped off before resolution |
| `N/A` | Not applicable / no resolution recorded |

### `sentiment`

Overall customer sentiment. `null` when the handling agent has
`enable_sentiment_analysis` disabled (see
[agents README](../agents/README.md#personalization_config)).

| Value |
|-------|
| `positive` |
| `neutral` |
| `negative` |

### `messages[].speaker` (detail only)

| Value | Description |
|-------|-------------|
| `ai` | Message from the AI agent |
| `user` | Message from the customer |

## Shared ticket shape

`reference`, `status`, `interface_type`, `agent_*`, `tags`, and timestamps appear
across list and detail. Detail adds the metadata, summary, and session-history
blocks.

| Field | Type | Notes |
|-------|------|-------|
| `ticket_id` | UUID | Ticket identifier |
| `reference` | string | Human-readable `TICK-XXXXX` |
| `status` | string | See [`status`](#status) |
| `interface_type` | string | `chat` \| `voice` |
| `customer_details` | string \| null | Free-text customer identifier (e.g. email/phone) |
| `tags` | string[] | Topic labels; may be empty |
| `agent_id` | UUID \| null | Handling agent; `null` for unassigned/manual |
| `agent_name` | string \| null | Snapshot of the agent name |
| `agent_type` | string \| null | `chat` \| `voice` \| null |
| `created_at` | ISO 8601 datetime | |

## Tags

`tags` are classification labels drawn from your organization's central
[tag catalog](../tags/README.md). The AI assigns them automatically during
post-close classification — there is no API to set ticket tags directly. Manage
the catalog (create/update/delete) via the [tags API](../tags/README.md); the
ticketing agent only ever assigns tags that currently exist in it.

Filter the ticket list by tag with the repeatable `tag` query parameter — see
[list-tickets.md](list-tickets.md#query-parameters).

**Related:** [../auth/login.md](../auth/login.md) · [../agents/README.md](../agents/README.md) · [../tags/README.md](../tags/README.md)
