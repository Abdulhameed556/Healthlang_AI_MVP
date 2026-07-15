# Dashboard API (`/api/v1/dashboard`)

JWT-protected, organization-scoped analytics for the product dashboard (ticket
volume and status breakdown).

Send `Authorization: Bearer <access_token>` on every call. For multi-org users,
optionally add `X-Organization-Id` — see
[organization context](../auth/organization-context.md).

| Doc | Method | Path | Who can call |
|-----|--------|------|--------------|
| [get-ticket-metrics.md](get-ticket-metrics.md) | GET | `/api/v1/dashboard/metrics` | All roles |

## Metrics semantics

Counts are based on ticket `created_at` within the selected date window.

### Summary buckets

| Field | Counts tickets with status |
|-------|----------------------------|
| `total` | All statuses in the window |
| `resolved` | `resolved` |
| `unresolved` | `open` or `unknown` |
| `transferred` | `transferred` |
| `failed` | `failed` |

### Weekday chart (`by_weekday`)

Always returns **seven fixed slots** (`mon` … `sun`). Each slot counts tickets
whose `created_at` falls on that weekday **within the filter window** (UTC).
For example, `preset=today` on a Thursday only populates the `thu` bucket.

## Standard envelope

```json
{
  "message": "…",
  "status_code": 200,
  "error": false,
  "data": { }
}
```

On failure, `error` is `true` and `data` is typically `null`.
