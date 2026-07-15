# DELETE /api/v1/integrations/{integration_id}

## URL

**Path:** `/api/v1/integrations/{integration_id}`

**Full URL:** `<base>/api/v1/integrations/{integration_id}`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/integrations/550e8400-e29b-41d4-a716-446655440000` |

**See also:** [integrations README](README.md) · [Freshchat README](freshchat/README.md)

## Summary

Disconnects and permanently deletes an integration for the caller's organization.
Also removes agent links, deletes linked Freshchat chat sessions, detaches those
sessions from any tickets (tickets themselves are kept), and clears cached
Freshchat Redis state for the integration.

## Auth

```http
Authorization: Bearer <access_token>
```

| Role | Can call |
|------|----------|
| `super_admin` | yes |
| `admin` | yes |
| `read_only` | no (403) |

## Path parameters

| Param | Type | Description |
|-------|------|-------------|
| `integration_id` | UUID | Integration to delete |

## Request body

None.

## Success (200)

```json
{
  "message": "Integration deleted successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "integration_id": "550e8400-e29b-41d4-a716-446655440000",
    "deleted_sessions": 12
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `integration_id` | UUID | Deleted integration id |
| `deleted_sessions` | integer | Number of linked chat sessions removed |

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 403 | `read_only` caller |
| 404 | Integration not found in the caller's organization |
| 422 | Malformed `integration_id` (not a UUID) |

## Frontend notes

- Confirm with the user before calling — deletion is irreversible.
- After success, clear Freshchat settings from local state and redirect away from
  integration management screens.
- Tickets created from deleted sessions remain in the [tickets list](../tickets/list-tickets.md);
  they are no longer linked to a live chat session.

## Code

- Endpoint: `src/presentation/api/v1/integrations/endpoints/delete_integration.py`
- Schemas: `src/presentation/api/v1/integrations/schemas.py`
- Use-case: `src/application/integrations/use_cases/delete_integration.py`
