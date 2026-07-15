# PATCH /api/v1/integrations/freshchat/settings

## URL

**Path:** `/api/v1/integrations/freshchat/settings`

**Full URL:** `<base>/api/v1/integrations/freshchat/settings`

| Environment | Base URL (`<base>`) | Example full URL |
|-------------|---------------------|------------------|
| Local | `http://localhost:8000` | `http://localhost:8000/api/v1/integrations/freshchat/settings` |
| Staging | `https://api-staging.example.com` | `https://api-staging.example.com/api/v1/integrations/freshchat/settings` |
| Production | `https://api.example.com` | `https://api.example.com/api/v1/integrations/freshchat/settings` |

## Summary

Updates the connected integration's sender agent, per-channel routing, handoff
group, and/or webhook public key **without re-entering credentials**. Only the
fields you send are changed (PATCH semantics).

## Auth

- Required: yes
- Header: `Authorization: Bearer <access_token>` (optional `X-Organization-Id`)
- Minimum role: `super_admin` or `admin`

## Request

- Content-Type: application/json
- **All fields optional.** Omitted fields are preserved. Sending a field replaces
  its stored value.

| Field | Type | Notes |
|-------|------|-------|
| `freshchat_agent_id` | string | New sender agent; re-validated against the account (uses the stored token). |
| `live_support_group_id` | string \| null | Handoff group. Send `null` to clear. |
| `channel_routing` | array | **Replaces the whole routing list** when provided. Same entry shape as [connect](connect.md#request). Each `agent_id` is validated to exist for the org. |
| `webhook_public_key` | string | New RSA public key (PEM). Send an **empty string** `""` to clear the stored key. |

**Sample body (change only the handoff group):**

```json
{
  "live_support_group_id": "60f78839-f714-45d2-b75c-dd1ef19f5e9d"
}
```

**Sample body (replace routing):**

```json
{
  "channel_routing": [
    {
      "channel_id": "3518515b-d192-4d9e-8b0e-cc4c8260c0a3",
      "agent_id": "b94f4bf0-d789-4d74-844c-1ff15530114e",
      "freshchat_channel_id": "818162"
    }
  ]
}
```

## Response envelope (backend product API)

### 200 OK

`data` is the [shared connection shape](README.md#shared-connection-shape-data)
(same as [get-settings](get-settings.md)).

```json
{
  "message": "Freshchat settings updated",
  "status_code": 200,
  "error": false,
  "data": { "...": "shared connection shape" }
}
```

### Error responses

| Status | When | Sample body |
|--------|------|-------------|
| 400 | New `freshchat_agent_id` not found in the account, or empty when provided | `{ "message": "Selected Freshchat agent was not found in this account", "status_code": 400, "error": true, "data": null }` |
| 401 | Missing/invalid session JWT | `{ "message": "...", "status_code": 401, "error": true, "data": null }` |
| 403 | Caller is not `super_admin`/`admin` | `{ "message": "...", "status_code": 403, "error": true, "data": null }` |
| 404 | Freshchat is not connected | `{ "message": "Freshchat is not connected", "status_code": 404, "error": true, "data": null }` |
| 422 | Schema validation (e.g. bad `agent_id` UUID in a routing entry) | `data` may contain `{ "errors": [...] }` |
| 502 | Freshchat API unreachable while validating a new agent | `{ "message": "...", "status_code": 502, "error": true, "data": null }` |

## Frontend notes

- **PATCH means partial:** to change one setting, send only that field. To leave
  routing untouched, omit `channel_routing` entirely (sending `[]` clears it).
- `channel_routing` is **replace-all**, not merge — send the full desired list.
- Clearing semantics: `live_support_group_id: null` removes the handoff group;
  `webhook_public_key: ""` removes the stored key.
- Credentials are never changed here; to rotate the API token use [connect](connect.md).

## Related

- [get-settings.md](get-settings.md) · [connect.md](connect.md) · [resources.md](resources.md)
