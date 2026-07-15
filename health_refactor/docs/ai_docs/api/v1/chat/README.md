# Chat API (`/api/v1/chat`)

HTTP endpoints for test and product chat sessions. One **session** maps to one
conversation thread; each **message** runs one full agent turn through the
[chat pipeline](../../architecture/chat-pipeline.md).

Routes are mounted on the **same server** as the product backend (`make dev-backend` →
`:8000`). The demo UI calls these at `/api/v1/chat/*`.

## Auth (v1)

Chat endpoints are **open** in the current internal demo — no JWT is required on
`/chat/sessions` or `/chat/messages`. Product auth applies to agent configuration
(create/publish/deploy) on `/api/v1/agents/*`.

Production frontends should treat auth requirements as TBD when customer-facing chat
ships.

## Response shape

Unlike product routes (`/agents`, `/api-tools`, …), chat responses are **flat JSON**
(Pydantic models), not the `{ message, status_code, error, data }` envelope.

Errors use FastAPI defaults, e.g. `{ "detail": "…" }` with HTTP status.

## Endpoints

| Doc | Method | Path | Summary |
|-----|--------|------|---------|
| [create-session.md](create-session.md) | POST | `/api/v1/chat/sessions` | Start a test session (`draft`, `version`, or `deployed`) |
| [send-message.md](send-message.md) | POST | `/api/v1/chat/messages` | Run one turn; get agent reply + state |

## Typical client flow

```
1. (optional) Edit agent draft in product UI
2. POST /api/v1/chat/sessions   config_source=draft|version|deployed
3. POST /api/v1/chat/messages     repeat with same session_id
```

To preview the **live** customer experience:

```
1. POST /api/v1/agents/{id}/publish
2. POST /api/v1/agents/{id}/versions/{version_id}/deploy
3. POST /api/v1/chat/sessions   config_source=deployed
4. POST /api/v1/chat/messages
```

## Shared field reference

### `conversation_state` (response)

Set by the orchestrator each turn. See
[chat pipeline — conversation state](../../architecture/chat-pipeline.md#conversation-state).

| Value | UI hint |
|-------|---------|
| `in_progress` | Normal chat |
| `waiting_on_customer` | Agent waiting on user |
| `pending_close` | Agent offered to end; confirm, continue, or wait for timeout — [planned](../../architecture/session-close-and-ticketing.md) |
| `end_conversation` | Session closing (user confirmed or timeout) |
| `transfer_to_live_support` | Offer live handoff |

### `mode` (create session request)

| Value | Usage |
|-------|-------|
| `test` | Builder preview and internal testing (default). No tickets on close; excluded from agent conversation history API |

Additional modes may be added for production channels.

### `config_source` (create session request)

| Value | Usage |
|-------|-------|
| `deployed` | Live deployed snapshot (default) |
| `version` | Specific published version (`version_id` required) |
| `draft` | Current unsaved agent configuration |

## Prerequisites

- `config_source=deployed` requires the agent to be **deployed**.
- `config_source=version` requires a valid published `version_id`.
- `config_source=draft` uses the live agent row (no publish/deploy needed).
- Postgres available (sessions and logs persist in shared DB).
- LLM env vars configured for orchestration (see `ai/src/core/config`).

## Code

| Piece | Path |
|-------|------|
| Router | `ai/src/presentation/api/v1/chat/router.py` |
| Schemas | `ai/src/presentation/api/v1/chat/schemas.py` |
| Create session | `ai/src/presentation/api/v1/chat/endpoints/session.py` |
| Send message | `ai/src/presentation/api/v1/chat/endpoints/message.py` |
| Pipeline | `ai/src/application/chat/pipeline.py` |
