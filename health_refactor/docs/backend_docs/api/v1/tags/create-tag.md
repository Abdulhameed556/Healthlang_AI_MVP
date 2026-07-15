# POST /api/v1/tags/

## URL

**Path:** `/api/v1/tags/`

**Full URL:** `<base>/api/v1/tags/`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/tags/` |

**See also:** [tags README](README.md) · [list-tags.md](list-tags.md) · [update-tag.md](update-tag.md)

## Summary

Creates an org-scoped classification tag. Once created, the tag becomes available
to the AI for labelling new tickets and as a [tickets list](../tickets/list-tickets.md)
filter value.

## Auth

```http
Authorization: Bearer <access_token>
```

| Role | Can call |
|------|----------|
| `super_admin` | yes |
| `admin` | yes |
| `read_only` | no (403) |

## Request body

`Content-Type: application/json`

```json
{
  "value": "refund_request",
  "description": "Customer is asking for their money back."
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `value` | yes | `snake_case`; unique per org; 1–64 chars; pattern `^[a-z0-9]+(_[a-z0-9]+)*$` |
| `description` | no | Default `""`; max 500 chars; helps the AI decide when the tag applies |

Field reference: [README — tag shape](README.md#tag-shape).

## Success (201)

```json
{
  "message": "Tag created successfully",
  "status_code": 201,
  "error": false,
  "data": {
    "tag_id": "550e8400-e29b-41d4-a716-446655440000",
    "value": "refund_request",
    "description": "Customer is asking for their money back.",
    "created_at": "2026-06-20T12:00:00Z",
    "updated_at": "2026-06-20T12:00:00Z"
  }
}
```

Response `data` matches [get-tag.md](get-tag.md). Server assigns `tag_id` and timestamps.

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 403 | `read_only` caller |
| 409 | Duplicate tag value in organization (case-insensitive) |
| 422 | Validation failure (e.g. non-snake_case `value`, empty `value`, too long) |

## Frontend notes

- Validate `value` as `snake_case` client-side before submitting to avoid a 422 round-trip.
- After create, store `data.tag_id` for edit and delete.

## Code

- Endpoint: `src/presentation/api/v1/tags/endpoints/create.py`
- Schemas: `src/presentation/api/v1/tags/schemas.py`
- Use-case: `src/application/tags/use_cases/create_tag.py`
