# GET /api/v1/agents/{agent_id}/conversations

## URL

**Path:** `/api/v1/agents/{agent_id}/conversations`

| Environment | Example full URL |
|-------------|-----------------|
| Local | `http://localhost:8000/api/v1/agents/{agent_id}/conversations` |

**See also:** [agents README](README.md) · [list-agents.md](list-agents.md)

## Summary

Returns paginated **production** chat sessions (with all conversation turns) for a
specific agent, scoped to the caller's organization. Builder preview sessions
(`metadata.mode = "test"`) are **excluded**. Used by the AI evaluation service
to load real customer conversations for `conversation_source="real"` eval runs.

## Auth

```http
Authorization: Bearer <access_token>
```

Optional `X-Organization-Id: <uuid>` for multi-org users — [organization-context.md](../auth/organization-context.md).

| Role | Can call |
|------|----------|
| `super_admin` | yes |
| `admin` | yes |
| `read_only` | yes |

## Path parameters

| Param | Type | Description |
|-------|------|-------------|
| `agent_id` | UUID | The agent whose sessions to retrieve |

## Query parameters

| Param | Type | Default | Limits | Description |
|-------|------|---------|--------|-------------|
| `page` | integer | `1` | ≥ 1 | Page number (1-based) |
| `page_size` | integer | `20` | 1–100 | Sessions per page |

**Example:** `GET /api/v1/agents/f99d70b3-…/conversations?page=1&page_size=20`

## Success (200)

```json
{
  "message": "Agent conversations retrieved successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "sessions": [
      {
        "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "agent_id": "f99d70b3-…",
        "status": "closed",
        "conversation_state": "finished",
        "started_at": "2026-06-20T10:30:00Z",
        "closed_at": "2026-06-20T10:45:00Z",
        "turns": [
          {
            "speaker": "user",
            "content": "My transfer has been pending for 2 days.",
            "sequence_index": 0,
            "spoken_at": "2026-06-20T10:30:05Z",
            "audio_url": null
          },
          {
            "speaker": "agent",
            "content": "I understand your concern. Let me check the status of your transfer.",
            "sequence_index": 1,
            "spoken_at": "2026-06-20T10:30:07Z",
            "audio_url": null
          }
        ]
      }
    ],
    "total": 42,
    "page": 1,
    "page_size": 20,
    "total_pages": 3
  }
}
```

### `data.sessions[]` fields

| Field | Type | Notes |
|-------|------|-------|
| `session_id` | UUID | Chat session identifier |
| `agent_id` | UUID | The agent that handled this session |
| `status` | string | `open` \| `closed` |
| `conversation_state` | string | `active` \| `finished` \| `escalated` |
| `started_at` | ISO 8601 datetime | When the session began |
| `closed_at` | ISO 8601 datetime \| null | When the session closed; null if still open |
| `turns` | array | Ordered conversation log entries |

### `turns[]` fields

| Field | Type | Notes |
|-------|------|-------|
| `speaker` | string | `user` or `agent` |
| `content` | string | The message text |
| `sequence_index` | integer | Zero-based position in the conversation |
| `spoken_at` | ISO 8601 datetime | When this turn was recorded |
| `audio_url` | string \| null | Pre-signed S3 URL for voice sessions; null for chat |

### Pagination fields

| Field | Type | Description |
|-------|------|-------------|
| `total` | integer | Total production sessions for this agent (test sessions excluded) |
| `page` | integer | Current page |
| `page_size` | integer | Page size used |
| `total_pages` | integer | `0` when `total` is `0` |

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 422 | Invalid `agent_id` format or invalid query parameters |

## Usage in chat evaluation

The AI service uses this endpoint's underlying data (via `LoadRealConversationsStep`) when running `conversation` mode evaluations with `conversation_source="real"`. The step queries the database directly rather than going through this HTTP endpoint, but the shape of data is identical. Test sessions (`metadata.mode = "test"`) are excluded in both paths.

To inspect what will be used in a real-source eval run before triggering it:

1. Call this endpoint to verify the agent has stored sessions
2. Check that sessions have `turns` with `speaker="user"` entries (agent-only sessions are skipped)
3. Trigger the eval with `conversation_source="real"` and `sample_size` ≤ `total`

## Code

- Endpoint: `backend/src/presentation/api/v1/agents/endpoints/conversations.py`
- Use-case: `backend/src/application/agents/use_cases/list_conversations.py`
- Eval step: `ai/src/application/chat_evaluation/steps/load_real_conversations.py`
