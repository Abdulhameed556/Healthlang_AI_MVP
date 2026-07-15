# GET /api/v1/tickets/{ticket_id}

## URL

**Path:** `/api/v1/tickets/{ticket_id}`

**Full URL:** `<base>/api/v1/tickets/{ticket_id}`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/tickets/550e8400-e29b-41d4-a716-446655440000` |

**See also:** [tickets README](README.md) · [list-tickets.md](list-tickets.md) · [create-ticket.md](create-ticket.md)

## Summary

Returns a single ticket's full detail: metadata (status, sentiment, resolution,
duration, originating number, tags), the handling agent (name, type, and
provisioned number for voice — `null` for chat), the AI summary, and the full
AI/user session history.

## Auth

```http
Authorization: Bearer <access_token>
```

| Role | Can call |
|------|----------|
| `super_admin` | yes |
| `admin` | yes |
| `read_only` | yes |

## Path parameters

| Param | Type | Description |
|-------|------|-------------|
| `ticket_id` | UUID | Ticket to load |

## Success (200)

```json
{
  "message": "Ticket retrieved successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
    "reference": "TICK-62YHW",
    "status": "resolved",
    "sentiment": "positive",
    "resolution": "resolved",
    "interface_type": "voice",
    "from_number": "+15551234567",
    "customer_details": "jane@example.com",
    "duration_seconds": 125,
    "tags": ["fees"],
    "created_at": "2026-06-18T10:00:00Z",
    "updated_at": "2026-06-18T10:02:05Z",
    "agent_id": "550e8400-e29b-41d4-a716-446655440010",
    "agent_name": "Support Bot",
    "agent_type": "voice",
    "agent_number": "+15557654321",
    "general_summary": "Customer asked why a fee was charged; agent explained and confirmed resolution.",
    "journey": "greeting -> fee question -> explanation -> resolved",
    "messages": [
      {
        "speaker": "user",
        "content": "Why was I charged a fee?",
        "sequence_index": 0,
        "spoken_at": "2026-06-18T10:00:05Z"
      },
      {
        "speaker": "ai",
        "content": "That fee covers the cross-border transfer. Here's the breakdown…",
        "sequence_index": 1,
        "spoken_at": "2026-06-18T10:00:12Z"
      }
    ]
  }
}
```

### Metadata fields

| Field | Type | Notes |
|-------|------|-------|
| `ticket_id` | UUID | Ticket identifier |
| `reference` | string | Human-readable `TICK-XXXXX` |
| `status` | string | See [statuses](README.md#status) |
| `sentiment` | string \| null | `null` when sentiment analysis is disabled for the agent |
| `resolution` | string \| null | See [resolution](README.md#resolution) |
| `interface_type` | string | `chat` \| `voice` |
| `from_number` | string \| null | Customer's originating number (voice) |
| `customer_details` | string \| null | Customer identifier (email/phone/etc.) |
| `duration_seconds` | integer \| null | Conversation duration in seconds |
| `tags` | string[] | Topic labels; may be empty |
| `created_at` | ISO 8601 datetime | |
| `updated_at` | ISO 8601 datetime | |

### Agent block

| Field | Type | Notes |
|-------|------|-------|
| `agent_id` | UUID \| null | `null` for manual/unassigned tickets |
| `agent_name` | string \| null | |
| `agent_type` | string \| null | `chat` \| `voice` \| null |
| `agent_number` | string \| null | Provisioned number; **always `null` for chat agents** |

### Summary block

| Field | Type | Notes |
|-------|------|-------|
| `general_summary` | string \| null | AI-generated summary of the conversation |
| `journey` | string \| null | Short step-by-step of the conversation flow |

### `messages[]` (session history, ordered)

| Field | Type | Notes |
|-------|------|-------|
| `speaker` | string | `ai` or `user` |
| `content` | string | Message text |
| `sequence_index` | integer | 0-based order within the session |
| `spoken_at` | ISO 8601 datetime | When the message was sent |

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 404 | Ticket not found or not in caller's organization |
| 422 | Invalid `ticket_id` format |

## Frontend notes

- `agent_number` is `null` for chat tickets — hide the number field when
  `interface_type` is `chat`.
- `sentiment` may be `null`; render a neutral/empty state rather than assuming a value.
- `messages` is already ordered by `sequence_index`; render as a transcript
  (`user` vs `ai`).
- For the tickets table, prefer [list-tickets.md](list-tickets.md) (lighter payload).

## Code

- Endpoint: `src/presentation/api/v1/tickets/endpoints/detail.py`
- Schemas: `src/presentation/api/v1/tickets/schemas.py`
- Use-case: `src/application/tickets/use_cases/get_ticket_detail.py`
