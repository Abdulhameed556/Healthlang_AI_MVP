# POST /api/v1/chat/sessions

## URL

**Path:** `/api/v1/chat/sessions`

**Full URL:** `<base>/api/v1/chat/sessions`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/chat/sessions` |

**See also:** [chat README](README.md) · [send-message.md](send-message.md) ·
[../../../architecture/chat-pipeline.md](../../../architecture/chat-pipeline.md)

## Summary

Creates a new builder **test** chat session for an agent. Loads the requested
configuration snapshot (deployed, a published version, or the live draft),
persists a `chat_sessions` row, and returns `session_id` for subsequent message
calls.

Test sessions (`mode: "test"`) do **not** create tickets on close. They are
excluded from the product [agent conversations](../../../../backend_docs/api/v1/agents/list-conversations.md)
list.

## Auth

No JWT in v1 demo. Callable by any client that can reach the API.

## Request body

`Content-Type: application/json`

```json
{
  "agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "mode": "test",
  "config_source": "deployed",
  "version_id": null
}
```

### Fields

| Field | Required | Notes |
|-------|----------|-------|
| `agent_id` | yes | UUID of the agent to chat with |
| `mode` | no | Default `"test"`. Stored in session `metadata.mode` |
| `config_source` | no | Default `"deployed"`. One of `deployed`, `version`, `draft` |
| `version_id` | when `config_source=version` | Published version UUID to preview |

### `config_source` values

| Value | Loads | Notes |
|-------|--------|-------|
| `deployed` | Live deployed snapshot | Agent must be deployed |
| `version` | Specific published version | Requires `version_id`; does not need to be deployed |
| `draft` | Current unsaved agent configuration | `agent_version_id` in response is `null`, `version_number` is `0` |

## Success (201)

Flat JSON body (not the product API envelope):

```json
{
  "session_id": "660e8400-e29b-41d4-a716-446655440001",
  "agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_version_id": "770e8400-e29b-41d4-a716-446655440002",
  "agent_name": "Support Bot",
  "version_number": 1,
  "mode": "test",
  "config_source": "deployed",
  "conversation_state": "in_progress"
}
```

| Field | Description |
|-------|-------------|
| `session_id` | Pass to every `POST /chat/messages` call |
| `agent_version_id` | Pinned version for `deployed` / `version`; `null` for `draft` |
| `agent_name` | From loaded snapshot |
| `version_number` | Version number (`0` for draft) |
| `config_source` | Echo of the requested snapshot source |
| `conversation_state` | Always starts as `in_progress` |

## Errors

| Status | When |
|--------|------|
| 404 | Agent or version not found |
| 409 | Agent not deployed when `config_source=deployed` |
| 422 | Invalid UUID, missing `version_id` for `config_source=version`, or body validation |

Example 409:

```json
{
  "detail": "Agent … has no deployed version"
}
```

## Frontend notes

- Use `config_source: "draft"` to preview unsaved builder changes without publishing.
- Use `config_source: "version"` + `version_id` to try a published version before deploy.
- The configuration is **pinned at create** — later deploys do not change an existing test session.
- Demo UI stores `session_id` in `localStorage` and clears stale ids on load.
- Session creation does **not** send an opening greeting; first agent text comes from
  the first `POST /chat/messages`.

## What happens internally

1. `load_runtime_for_config(agent_id, config_source, version_id)` — reads draft, version, or deployed snapshot.
2. `ChatSessionStore.create(...)` — inserts session with org, agent, version ids and `metadata.mode` / `metadata.config_source`.
3. Each message turn calls `load_runtime_for_session(session)` so the pinned snapshot is honored.
4. Closing a test session does **not** enqueue post-close ticketing.

## Code

- Endpoint: `ai/src/presentation/api/v1/chat/endpoints/session.py`
- Use-case: `ai/src/application/chat/create_session.py`
- Runtime loader: `ai/src/infrastructure/chat_system/v1/agents/scenario_agent/runtime_loader.py`
- Test mode gates: `ai/src/application/chat/session_mode.py`
