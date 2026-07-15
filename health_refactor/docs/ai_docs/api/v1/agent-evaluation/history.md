# GET /ai/api/v1/chat-evaluation/runs

## URL

**Path:** `/ai/api/v1/chat-evaluation/runs`

| Environment | Full URL |
|-------------|----------|
| Local | `http://localhost:8001/ai/api/v1/chat-evaluation/runs?agent_id={agent_id}` |

**See also:** [run.md](run.md) — start a run, [status.md](status.md) — full results, [README.md](README.md) — overview

---

## Summary

Returns a **paginated** list of past evaluation runs for an agent, newest first. Only summary-level data is returned — no conversation turns or per-case details. To get full results for a specific run, call `GET /status/{run_id}`.

---

## Auth

No authentication required.

---

## Query parameters

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `agent_id` | UUID string | — | Filter runs by agent. Omit to return all runs across all agents. |
| `page` | integer | `1` | Page number (1-based). |
| `page_size` | integer | `20` | Runs per page. Range: 1–100. |

---

## Example request

```bash
curl "http://localhost:8001/ai/api/v1/chat-evaluation/runs?agent_id=dddddddd-dddd-4000-8000-dddddddddddd&page=1&page_size=20"
```

---

## Response (200)

```json
{
  "runs": [
    {
      "run_id": "eval-run-2026-07-02-abc123",
      "eval_mode": "conversation",
      "agent_id": "dddddddd-dddd-4000-8000-dddddddddddd",
      "status": "completed",
      "created_at": "2026-07-02T10:30:00+00:00",
      "aggregate_scores": {
        "conversation_quality": 0.81,
        "judge_score": 0.75,
        "scenarios_covered": 3.0
      },
      "error": ""
    },
    {
      "run_id": "eval-run-2026-07-01-xyz789",
      "eval_mode": "conversation",
      "agent_id": "dddddddd-dddd-4000-8000-dddddddddddd",
      "status": "failed",
      "created_at": "2026-07-01T09:30:00+00:00",
      "aggregate_scores": {},
      "error": "Agent has no deployed version."
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

---

## Response fields

### Top level

| Field | Type | Notes |
|-------|------|-------|
| `runs` | array | Evaluation run summaries for the current page, newest first |
| `total` | integer | Total number of runs matching the query |
| `page` | integer | Current page number (1-based) |
| `page_size` | integer | Number of runs per page |
| `total_pages` | integer | Total pages. `0` when `total` is `0`. |

### Per run

| Field | Type | Notes |
|-------|------|-------|
| `run_id` | string | Use this to fetch full results via `GET /status/{run_id}` |
| `eval_mode` | string | Always `"conversation"` for agent evaluation runs |
| `agent_id` | string\|null | UUID of the agent evaluated |
| `status` | string | `pending`, `running`, `completed`, or `failed` |
| `created_at` | string | ISO 8601 timestamp (UTC) when the run was created |
| `aggregate_scores` | object | Summary scores — empty `{}` for pending/running/failed runs |
| `error` | string | Error message when `status=failed`. Empty string otherwise. |

---

## Errors

| Status | When |
|--------|------|
| 500 | Unexpected server error |

---

## Code

- Endpoint: `ai/src/presentation/api/v1/chat_evaluation/endpoints/run.py` (`GET ""` handler)
- S3 store: `ai/src/infrastructure/chat_evaluation/s3_run_store.py` (`list()` method)
- Schema: `ai/src/presentation/api/v1/chat_evaluation/schemas.py` (`ListRunsResponse`, `RunSummaryResponse`)
