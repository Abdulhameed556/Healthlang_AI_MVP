# POST /api/v1/chat/messages

## URL

**Path:** `/api/v1/chat/messages`

**Full URL:** `<base>/api/v1/chat/messages`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/chat/messages` |

**See also:** [chat README](README.md) · [create-session.md](create-session.md) ·
[../../../architecture/chat-pipeline.md](../../../architecture/chat-pipeline.md)

## Summary

Runs **one chat turn** for an existing session: loads history, applies guardrails,
routes scenario, builds system prompt from the deployed agent snapshot, runs
LangGraph orchestration (with optional API tools), and returns the agent reply.

This is a **request/response** call in v1 (not SSE streaming).

## Auth

No JWT in v1 demo.

## Request body

`Content-Type: application/json`

```json
{
  "session_id": "660e8400-e29b-41d4-a716-446655440001",
  "message": "Can you look up my account?"
}
```

### Fields

| Field | Required | Limits |
|-------|----------|--------|
| `session_id` | yes | UUID from create session |
| `message` | yes | 1–8000 characters (trimmed) |

## Success (200)

```json
{
  "session_id": "660e8400-e29b-41d4-a716-446655440001",
  "agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "version_id": "770e8400-e29b-41d4-a716-446655440002",
  "message": "I'd be happy to help. Could you share your phone number?",
  "conversation_state": "waiting_on_customer",
  "pipeline_stopped": null,
  "timing_ms": {
    "session_load": 12.5,
    "runtime_load": 8.2,
    "input_guardrail": 450.0,
    "scenario_routing": 320.0,
    "orchestration": 2100.0,
    "output_guardrail": 0.0,
    "total": 2891.0
  },
  "turn_metadata": {
    "session_id": "660e8400-e29b-41d4-a716-446655440001",
    "agent_id": "550e8400-e29b-41d4-a716-446655440000",
    "version_id": "770e8400-e29b-41d4-a716-446655440002",
    "routing": { "scenario_id": "…", "reason": "…" },
    "orchestration": { "parse_success": true, "tool_activity": [] },
    "session_facts": { "previous": {}, "delta": {}, "merged": {} },
    "timing_ms": { }
  }
}
```

### Response fields

| Field | Description |
|-------|-------------|
| `message` | Text shown to the user (after output guardrail if enabled) |
| `conversation_state` | Updated session state — drive UI prompts (end chat, transfer, etc.) |
| `pipeline_stopped` | Set when input guardrail blocks (e.g. `"input_guardrail_block"`); otherwise `null` |
| `timing_ms` | Step timings in milliseconds |
| `turn_metadata` | Debug/observability: routing, tools, guardrails, session facts |

### `conversation_state` values

| Value | Typical UI behavior |
|-------|---------------------|
| `in_progress` | Continue chat normally |
| `waiting_on_customer` | Continue chat; agent asked a question |
| `end_conversation` | Prompt user to confirm session end |
| `transfer_to_live_support` | Prompt user to confirm live handoff |

## Errors

| Status | When |
|--------|------|
| 404 | Unknown `session_id` |
| 422 | Invalid UUID, empty message, or message too long |
| 409 / 410 | **Planned:** session already closed — client must start a new session |

Example 404:

```json
{
  "detail": "Chat session not found"
}
```

**Planned** closed-session response (see [session-close-and-ticketing.md](../../../architecture/session-close-and-ticketing.md)):

```json
{
  "detail": "This conversation has ended. Please start a new session to continue.",
  "code": "session_closed",
  "session_id": "660e8400-e29b-41d4-a716-446655440001",
  "closed_at": "2026-06-17T12:05:00Z",
  "close_reason": "auto_timeout"
}
```

## Frontend notes

- Reuse the same `session_id` for the whole conversation.
- Display `message` as the agent bubble; use `timing_ms.total` for response time if desired.
- Watch `conversation_state` each turn — demo UI shows a sidebar pill and action prompts
  for `pending_close` (planned), `end_conversation`, and `transfer_to_live_support`.
- If send-message returns `session_closed`, disable the composer and prompt the user to
  start a new session (`POST /api/v1/chat/sessions`).
- `turn_metadata` is safe to log in dev; omit from customer UI in production.
- After agent **re-deploy**, existing sessions keep the **version pinned at create time**.
  Start a new session to pick up a new deploy.

## Pipeline (one turn)

See [chat-pipeline.md](../../../architecture/chat-pipeline.md) for the full diagram.

1. Load session + history  
2. Load deployed runtime (brand, rules, scenarios, tools)  
3. Input guardrail  
4. Scenario routing  
5. Build system prompt (brand identity, timezone, tone, rules, session facts, tools)  
6. LangGraph: LLM ↔ API tools  
7. Output guardrail  
8. Persist user + agent turns + merged session facts  

## Code

- Endpoint: `ai/src/presentation/api/v1/chat/endpoints/message.py`
- Pipeline: `ai/src/application/chat/pipeline.py`
- Settings: `ai/src/application/chat/settings.py` (`DEFAULT_CHAT_CONFIG`)
- Orchestration graph: `ai/src/infrastructure/chat_system/v1/orchestration/graph.py`
