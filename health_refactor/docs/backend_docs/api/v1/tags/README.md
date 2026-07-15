# Tags API (`/api/v1/tags`)

JWT-protected, organization-scoped catalog of classification **tags**. Tags are a
central, org-wide list. The AI ticketing agent reads the current catalog when a
session closes and assigns matching tags to the ticket — tags are **not** attached
to agents and are never set on tickets directly. Filter the
[tickets list](../tickets/list-tickets.md) by tag to find labelled tickets.

Send `Authorization: Bearer <access_token>` on every call. Obtain the token from
[login](../auth/login.md) or [Google login](../auth/google-login.md). For multi-org
users, optionally add `X-Organization-Id` — see
[organization context](../auth/organization-context.md).

| Doc | Method | Path | Who can call |
|-----|--------|------|--------------|
| [list-tags.md](list-tags.md) | GET | `/api/v1/tags/` | All roles |
| [create-tag.md](create-tag.md) | POST | `/api/v1/tags/` | `super_admin`, `admin` |
| [get-tag.md](get-tag.md) | GET | `/api/v1/tags/{tag_id}` | All roles |
| [update-tag.md](update-tag.md) | PUT | `/api/v1/tags/{tag_id}` | `super_admin`, `admin` |
| [delete-tag.md](delete-tag.md) | DELETE | `/api/v1/tags/{tag_id}` | `super_admin`, `admin` |

## How tags flow through the system

1. **Manage the catalog** — admins create/update/delete tags here.
2. **AI classifies** — when a chat/voice session closes, the ticketing agent is
   given the current catalog and assigns zero or more tags to the new ticket. It
   can only ever pick tags that exist in the catalog at that moment.
3. **Filter tickets** — the [tickets list](../tickets/list-tickets.md) accepts a
   repeatable `tag` query parameter to find tickets carrying given tags.

Deleting a tag from the catalog stops the AI from assigning it going forward and
removes it as a valid ticket filter, but does not retroactively strip it from
tickets that were already labelled with it.

## Response envelope

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

## Tag shape

Create, update, and get return the same tag `data` object.

| Field | Type | Notes |
|-------|------|-------|
| `tag_id` | UUID | Server-assigned identifier |
| `value` | string | `snake_case` label; unique per org; 1–64 chars |
| `description` | string | Optional context for the AI; `""` when unset; max 500 chars |
| `created_at` | ISO 8601 datetime | |
| `updated_at` | ISO 8601 datetime | |

### `value` rules

- Must be **snake_case**: lowercase alphanumeric groups joined by single
  underscores — pattern `^[a-z0-9]+(_[a-z0-9]+)*$` (e.g. `refund_request`, `fees`,
  `kyc_issue`).
- Unique per organization (case-insensitive); duplicates → `409`.
- Non-conforming values → `422`.

### Full tag example (`data` on create / get / update)

```json
{
  "tag_id": "550e8400-e29b-41d4-a716-446655440000",
  "value": "refund_request",
  "description": "Customer is asking for their money back.",
  "created_at": "2026-06-20T12:00:00Z",
  "updated_at": "2026-06-20T12:00:00Z"
}
```

## Typical UI flow

1. **List** the catalog → [list-tags.md](list-tags.md)
2. **Create** / **update** tags → [create-tag.md](create-tag.md) / [update-tag.md](update-tag.md)
3. **Delete** unused tags → [delete-tag.md](delete-tag.md)
4. **See results** — the AI labels new tickets; filter them via the
   [tickets list](../tickets/list-tickets.md#query-parameters) `tag` param.

**Related:** [../tickets/README.md](../tickets/README.md) · [../auth/login.md](../auth/login.md)
