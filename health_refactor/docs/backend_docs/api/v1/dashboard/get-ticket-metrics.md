# GET /api/v1/dashboard/metrics

## URL

**Path:** `/api/v1/dashboard/metrics`

**Full URL:** `<base>/api/v1/dashboard/metrics`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/dashboard/metrics` |

**See also:** [dashboard README](README.md) · [tickets list](../tickets/list-tickets.md)

## Summary

Returns ticket summary counts and a Monday–Sunday breakdown for the caller's
organization. Use this for dashboard KPI cards and the weekday chart.

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

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `preset` | string | `last_7_days` | `today` \| `last_7_days` \| `last_30_days` \| `custom` |
| `custom_start` | date (`YYYY-MM-DD`) | — | Required when `preset=custom` (inclusive UTC start) |
| `custom_end` | date (`YYYY-MM-DD`) | — | Required when `preset=custom` (inclusive UTC end) |

Notes:

- Rolling presets (`last_7_days`, `last_30_days`) end at the current server time (UTC).
- `today` is the current UTC calendar day from midnight through now.
- `custom` uses inclusive full UTC days for `custom_start` and `custom_end`.
- `custom_start` must be on or before `custom_end`.

**Examples:**

- `GET /api/v1/dashboard/metrics`
- `GET /api/v1/dashboard/metrics?preset=today`
- `GET /api/v1/dashboard/metrics?preset=custom&custom_start=2026-06-01&custom_end=2026-06-30`

## Success (200)

```json
{
  "message": "Dashboard metrics retrieved successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "summary": {
      "total": 42,
      "resolved": 20,
      "unresolved": 15,
      "transferred": 5,
      "failed": 2
    },
    "by_weekday": [
      {
        "weekday": "mon",
        "counts": {
          "total": 6,
          "resolved": 3,
          "unresolved": 2,
          "transferred": 1,
          "failed": 0
        }
      },
      {
        "weekday": "tue",
        "counts": {
          "total": 0,
          "resolved": 0,
          "unresolved": 0,
          "transferred": 0,
          "failed": 0
        }
      }
    ]
  }
}
```

`by_weekday` always contains seven entries in order: `mon`, `tue`, `wed`, `thu`,
`fri`, `sat`, `sun`. Slots with no tickets in the window have zero counts.

### Summary field meanings

See [README.md](README.md#metrics-semantics).

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 422 | Invalid `preset`, missing custom dates when `preset=custom`, or `custom_start` after `custom_end` |

## Frontend notes

- Default the date picker to `last_7_days` to match the API default.
- When the user picks a custom range, send all three query params:
  `preset=custom&custom_start=…&custom_end=…`.
- Render all seven weekday slots even when counts are zero so the chart layout
  stays stable.

## Code

- Endpoint: `src/presentation/api/v1/dashboard/endpoints/metrics.py`
- Schemas: `src/presentation/api/v1/dashboard/schemas.py`
- Use-case: `src/application/dashboard/use_cases/get_ticket_metrics.py`
