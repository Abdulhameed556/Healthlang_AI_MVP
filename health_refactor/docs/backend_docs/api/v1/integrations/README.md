# Integrations API (`/api/v1/integrations`)

Organization-scoped routes for third-party channel integrations and agent links.

Send `Authorization: Bearer <access_token>` on every JWT route. For multi-org users,
optionally add `X-Organization-Id` — see
[organization context](../auth/organization-context.md).

| Doc | Method | Path | Who can call |
|-----|--------|------|--------------|
| [delete-integration.md](delete-integration.md) | DELETE | `/api/v1/integrations/{integration_id}` | `super_admin`, `admin` |
| [freshchat/README.md](freshchat/README.md) | — | `/api/v1/integrations/freshchat/...` | See Freshchat docs |

## Provider-specific docs

- **Freshchat** — [freshchat/README.md](freshchat/README.md) (connect, settings, webhook)

## Standard envelope

JWT routes return:

```json
{
  "message": "…",
  "status_code": 200,
  "error": false,
  "data": { }
}
```

On failure, `error` is `true` and `data` is typically `null`.
