# POST /api/v1/tickets/

## URL

**Path:** `/api/v1/tickets/`

**Full URL:** `<base>/api/v1/tickets/`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/tickets/` |

**See also:** [tickets README](README.md) · [list-tickets.md](list-tickets.md) · [get-ticket.md](get-ticket.md)

## Summary

Manually creates a standalone ticket (not tied to a chat session) for the caller's
organization. A unique `TICK-XXXXX` `reference` is generated automatically. Use this
for tickets logged outside the AI flow; session tickets are created automatically by
the post-close pipeline.

## Auth

```http
Authorization: Bearer <access_token>
```

| Role | Can call |
|------|----------|
| `super_admin` | yes |
| `admin` | yes |
| `read_only` | yes |

## Request body

`Content-Type: application/json`

```json
{
  "interface_type": "voice",
  "status": "resolved",
  "agent_id": "550e8400-e29b-41d4-a716-446655440010",
  "resolution": "N/A",
  "sentiment": "positive",
  "from_number": "+15551234567",
  "assigned_number": "+15557654321",
  "customer_details": "jane@example.com",
  "duration_seconds": 125,
  "tags": ["fees"]
}
```

### Fields

| Field | Type | Required | Limits / notes |
|-------|------|----------|----------------|
| `interface_type` | string | yes | `chat` \| `voice` |
| `status` | string | yes | See [statuses](README.md#status) |
| `agent_id` | UUID \| null | no | Must belong to the caller's organization when supplied |
| `resolution` | string \| null | no | See [resolution](README.md#resolution) |
| `sentiment` | string \| null | no | `positive` \| `neutral` \| `negative` |
| `from_number` | string \| null | no | max 30; customer's originating number |
| `assigned_number` | string \| null | no | max 30; provisioned number handling the ticket |
| `customer_details` | string \| null | no | max 255 |
| `duration_seconds` | integer \| null | no | ≥ 0 |
| `tags` | string[] | no | Default `[]` |

The `reference` is **not** accepted in the request — it is generated server-side.

## Success (201)

```json
{
  "message": "Ticket created successfully",
  "status_code": 201,
  "error": false,
  "data": {
    "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
    "reference": "TICK-62YHW",
    "status": "resolved",
    "interface_type": "voice",
    "agent_id": "550e8400-e29b-41d4-a716-446655440010",
    "customer_details": "jane@example.com",
    "tags": ["fees"],
    "created_at": "2026-06-18T10:00:00Z"
  }
}
```

### `data` fields

| Field | Type | Notes |
|-------|------|-------|
| `ticket_id` | UUID | Server-assigned identifier |
| `reference` | string | Server-generated `TICK-XXXXX` |
| `status` | string | Echoes the submitted status |
| `interface_type` | string | `chat` \| `voice` |
| `agent_id` | UUID \| null | Echoes the submitted agent, if any |
| `customer_details` | string \| null | |
| `tags` | string[] | |
| `created_at` | ISO 8601 datetime | |

Load [get-ticket.md](get-ticket.md) with the returned `ticket_id` for full detail.

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 404 | `agent_id` supplied but not found in the caller's organization |
| 422 | Validation failure (invalid enum value, field limits, malformed UUID, negative `duration_seconds`) |

## Frontend notes

- Do not send `reference`; display the one returned in `data`.
- `agent_id` is optional — omit for tickets not linked to an agent.
- After create, you can redirect to the detail view using `data.ticket_id`.

## Code

- Endpoint: `src/presentation/api/v1/tickets/endpoints/create.py`
- Schemas: `src/presentation/api/v1/tickets/schemas.py`
- Use-case: `src/application/tickets/use_cases/create_ticket.py`
