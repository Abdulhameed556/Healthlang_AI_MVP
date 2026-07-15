# GET /ai/api/v1/chat-evaluation/runs

## URL

**Path:** `/ai/api/v1/chat-evaluation/runs`

| Environment | Example full URL |
|-------------|-----------------|
| Local | `http://localhost:8001/api/v1/chat-evaluation/runs` |

**See also:** [run.md](run.md) — start a run, [status.md](status.md) — fetch full results, [README.md](README.md) — overview

## Summary

Returns a **paginated summary list** of past evaluation runs for a given agent, newest first.

Only aggregate-level data is included per run — use `GET /status/{run_id}` to fetch the full case results and per-turn detail for a specific run.

Results are fetched from S3. Falls back to in-memory if `AWS_S3_BUCKET` is not configured.

## Auth

No authentication required.

## Query parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `agent_id` | string (UUID) | — | Filter by agent. Omit to list across all agents. |
| `page` | integer | `1` | Page number (1-based). |
| `page_size` | integer | `20` | Runs per page. Range: 1–100. |

## Response

**200 OK**

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
        "kb_utilization": 0.84,
        "rule_adherence": 0.90,
        "scenarios_covered": 5,
        "judge_score": 0.75
      },
      "error": ""
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

### Response fields

| Field | Type | Description |
|-------|------|-------------|
| `runs` | array | Run summaries for the current page, newest first |
| `total` | integer | Total number of runs matching the query |
| `page` | integer | Current page (1-based) |
| `page_size` | integer | Runs per page |
| `total_pages` | integer | Total pages. `0` when `total` is `0`. |
| `runs[].run_id` | string | Unique run identifier — use to fetch full results via `/status/{run_id}` |
| `runs[].eval_mode` | string | `conversation`, `e2e`, `input_guardrail`, etc. |
| `runs[].agent_id` | string or null | Agent evaluated; null for guardrail-only modes |
| `runs[].status` | string | `pending`, `running`, `completed`, or `failed` |
| `runs[].created_at` | string | ISO 8601 timestamp when the run was created |
| `runs[].aggregate_scores` | object | Summary metrics — empty `{}` until run completes |
| `runs[].error` | string | Error message when status is `failed`; empty otherwise |

> **Note:** `case_results` (per-turn detail) is **not** included in list responses. Fetch `GET /status/{run_id}` for the full report.

## Example

```bash
# List runs for an agent, page 1
curl "http://localhost:8001/ai/api/v1/chat-evaluation/runs?agent_id=dddddddd-dddd-4000-8000-dddddddddddd&page=1&page_size=20"
```
