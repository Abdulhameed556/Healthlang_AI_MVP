# GET /api/v1/tickets/

## URL

**Path:** `/api/v1/tickets/`

**Full URL:** `<base>/api/v1/tickets/`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/tickets/` |

**See also:** [tickets README](README.md) · [get-ticket.md](get-ticket.md) · [create-ticket.md](create-ticket.md)

## Summary

Returns a paginated list of tickets for the caller's organization, with filtering
and free-text search. Use this for the tickets table; call [get-ticket.md](get-ticket.md)
for full metadata, summary, and session history.

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

## Query parameters

All parameters are optional. Filters combine with **AND**.

| Param | Type | Default | Limits | Description |
|-------|------|---------|--------|-------------|
| `agent_id` | UUID | — | — | Filter by handling agent |
| `interface_type` | string | — | `chat` \| `voice` | Filter by channel |
| `status` | string | — | see [statuses](README.md#status) | Filter by ticket status |
| `customer_details` | string | — | — | Substring match on customer details |
| `date_range` | string | — | `last_24_hours` \| `last_7_days` \| `last_30_days` \| `last_90_days` | Relative window on `created_at` |
| `created_after` | ISO 8601 datetime | — | — | Only tickets at/after this timestamp |
| `created_before` | ISO 8601 datetime | — | — | Only tickets at/before this timestamp |
| `tag` | string (repeatable) | — | must exist in the org [tag catalog](../tags/README.md) | Filter by tag value(s); matches tickets with **ANY** of them |
| `search` | string | — | — | Free-text over `reference`, `customer_details`, `status`, and agent name |
| `page` | integer | `1` | ≥ 1 | Page number (1-based) |
| `page_size` | integer | `20` | 1–100 | Tickets per page |

Notes:

- `date_range` is a convenience preset resolved server-side to `created_after`.
  When both `date_range` and explicit `created_after`/`created_before` are sent,
  the explicit bounds also apply.
- `search` is case-insensitive and matches partial values.
- `tag` is **repeatable** — send `?tag=fees&tag=refund_request` to match tickets
  carrying any of those tags. Values are matched case-insensitively against the
  org [tag catalog](../tags/README.md) and normalized to their canonical stored
  form. Any value **not** in the catalog rejects the whole request with `422`.
  Tags are assigned to tickets by the AI during classification — manage the
  catalog via the [tags API](../tags/README.md).

**Example:** `GET /api/v1/tickets/?status=open&interface_type=voice&date_range=last_7_days&tag=fees&tag=refund_request&page=1&page_size=20`

## Success (200)

```json
{
  "message": "Tickets retrieved successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "tickets": [
      {
        "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
        "reference": "TICK-62YHW",
        "status": "resolved",
        "interface_type": "voice",
        "customer_details": "jane@example.com",
        "tags": ["fees"],
        "agent_id": "550e8400-e29b-41d4-a716-446655440010",
        "agent_name": "Support Bot",
        "agent_type": "voice",
        "created_at": "2026-06-18T10:00:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
}
```

### `data.tickets[]` fields

| Field | Type | Notes |
|-------|------|-------|
| `ticket_id` | UUID | Ticket identifier |
| `reference` | string | Human-readable `TICK-XXXXX` |
| `status` | string | See [statuses](README.md#status) |
| `interface_type` | string | `chat` \| `voice` |
| `customer_details` | string \| null | Customer identifier (email/phone/etc.) |
| `tags` | string[] | Topic labels; may be empty |
| `agent_id` | UUID \| null | `null` for manual/unassigned tickets |
| `agent_name` | string \| null | |
| `agent_type` | string \| null | `chat` \| `voice` \| null |
| `created_at` | ISO 8601 datetime | |

### Pagination fields

| Field | Type | Description |
|-------|------|-------------|
| `total` | integer | Total tickets matching the filters |
| `page` | integer | Current page |
| `page_size` | integer | Page size used |
| `total_pages` | integer | `0` when `total` is `0` |

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 422 | Invalid query parameter (e.g. unknown `status`, `page=0`, malformed `agent_id`, or a `tag` not in the org catalog) |

## Frontend notes

- Default to `page=1` and `page_size=20`; expose page size up to 100.
- Use `total_pages` for pagination UI; do not assume a fixed page count.
- The same endpoint powers both the filtered table and the search box — send
  `search` for free-text and/or the discrete filters; they combine.
- List rows omit metadata, summary, and history — load [get-ticket.md](get-ticket.md)
  for the detail view.

## Code

- Endpoint: `src/presentation/api/v1/tickets/endpoints/list.py`
- Schemas: `src/presentation/api/v1/tickets/schemas.py`
- Use-case: `src/application/tickets/use_cases/list_tickets.py`
