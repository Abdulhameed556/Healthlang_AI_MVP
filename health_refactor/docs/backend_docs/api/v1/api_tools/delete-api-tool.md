# DELETE /api/v1/api-tools/{api_tool_id}

## URL

**Path:** `/api/v1/api-tools/{api_tool_id}`

**Full URL:** `<base>/api/v1/api-tools/{api_tool_id}`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/api-tools/550e8400-e29b-41d4-a716-446655440000` |

**See also:** [api_tools README](README.md) · [list-api-tools.md](list-api-tools.md)

## Summary

Deletes an API tool. Fails with **409** when the tool is still linked to one or more agents
(via `api_tool_ids` on agent configuration).

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
| `api_tool_id` | UUID | Tool to delete |

## Request body

None.

## Success (200)

```json
{
  "message": "API tool deleted successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "api_tool_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 403 | `read_only` caller |
| 404 | Tool not found or not in caller's organization |
| 409 | Tool is attached to an agent — remove from agent `api_tool_ids` first |
| 422 | Invalid `api_tool_id` format |

## Frontend notes

- Confirm with the user before calling — deletion is irreversible.
- On 409, show which agents use the tool (load agent configs) or prompt to unlink first.
- After success, remove the tool from local state and navigate to [list-api-tools.md](list-api-tools.md).

## Code

- Endpoint: `src/presentation/api/v1/api_tools/endpoints/delete.py`
- Use-case: `src/application/api_tools/use_cases/delete_api_tool.py`
