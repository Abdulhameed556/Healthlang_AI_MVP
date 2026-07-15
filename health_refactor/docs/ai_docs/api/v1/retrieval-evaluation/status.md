# GET /ai/api/v1/retrieval-evaluation/{run_id}

## URL

**Path:** `/ai/api/v1/retrieval-evaluation/{run_id}`

| Environment | Example full URL |
|-------------|-----------------|
| Local | `http://localhost:8001/ai/api/v1/retrieval-evaluation/{run_id}` |
| Staging | `https://ai.staging.afriex.io/ai/api/v1/retrieval-evaluation/{run_id}` |
| Production | `https://ai.afriex.io/ai/api/v1/retrieval-evaluation/{run_id}` |

**See also:** [run.md](run.md) — start a batch, [README.md](README.md) — metric descriptions and status progression

## Summary

Returns the current status and full results of a batch retrieval-evaluation run. Suitable for polling until the run completes.

Results (`entry_reports`, `aggregate_scores`) are populated once `status` is `completed`. While the run is `pending` or `running`, these fields are empty.

## Auth

No JWT required (same as the run endpoint).

## Path parameters

| Parameter | Type | Notes |
|-----------|------|-------|
| `run_id` | string | The `run_id` returned by `POST /run`. |

## Success (200) — run completed

```json
{
  "run_id": "eval-2025-01-15-abc123",
  "agent_id": "dddddddd-dddd-4000-8000-dddddddddddd",
  "kb_entry_ids": [
    "aaaaaaaa-aaaa-4000-8000-aaaaaaaaaaaa",
    "bbbbbbbb-bbbb-4000-8000-bbbbbbbbbbbb"
  ],
  "status": "completed",
  "aggregate_scores": {
    "contextual_relevancy": 0.87,
    "contextual_precision": 0.91,
    "contextual_recall": 0.78
  },
  "entry_reports": [
    {
      "kb_entry_id": "aaaaaaaa-aaaa-4000-8000-aaaaaaaaaaaa",
      "status": "completed",
      "aggregate_scores": {
        "contextual_relevancy": 0.85,
        "contextual_precision": 0.90,
        "contextual_recall": 0.75
      },
      "question_results": [
        {
          "question": "What is the refund policy?",
          "expected_output": "Returns are accepted within 30 days with a valid receipt.",
          "retrieved_context": [
            "Our return policy allows refunds within 30 days...",
            "Receipts must be presented at the time of return..."
          ],
          "metrics": [
            {
              "name": "contextual_relevancy",
              "score": 0.85,
              "threshold": 0.7,
              "success": true,
              "reason": "Retrieved chunks are highly relevant to the question."
            },
            {
              "name": "contextual_precision",
              "score": 0.90,
              "threshold": 0.7,
              "success": true,
              "reason": "Most relevant chunk appeared in position 1."
            },
            {
              "name": "contextual_recall",
              "score": 0.75,
              "threshold": 0.7,
              "success": true,
              "reason": "Context covers the main points of the expected answer."
            }
          ]
        }
      ],
      "error": ""
    }
  ],
  "error": ""
}
```

### Top-level response fields

| Field | Notes |
|-------|-------|
| `run_id` | Matches the `run_id` from `POST /run`. |
| `agent_id` | The agent evaluated. |
| `kb_entry_ids` | All entry IDs in this batch. |
| `status` | `pending` / `running` / `completed` / `failed` (see [README](README.md)). |
| `aggregate_scores` | Mean scores across all completed entries. Empty `{}` while still running. |
| `entry_reports` | Per-entry results. Empty `[]` while still running. |
| `error` | Non-empty only when the entire batch failed. |

### `entry_reports[].question_results[].metrics[]` fields

| Field | Notes |
|-------|-------|
| `name` | `contextual_relevancy`, `contextual_precision`, or `contextual_recall`. |
| `score` | 0–1. Higher is better. |
| `threshold` | Minimum passing score (default 0.7). |
| `success` | `true` when `score >= threshold`. |
| `reason` | Natural-language explanation from the judge LLM. |

## Success (200) — run still in progress

```json
{
  "run_id": "eval-2025-01-15-abc123",
  "agent_id": "dddddddd-dddd-4000-8000-dddddddddddd",
  "kb_entry_ids": ["aaaaaaaa-aaaa-4000-8000-aaaaaaaaaaaa"],
  "status": "running",
  "aggregate_scores": {},
  "entry_reports": [],
  "error": ""
}
```

## Success (200) — partial failure (some entries failed)

Batch `status` is `"completed"` (not `"failed"`) when at least one entry succeeded. Failed entries appear in `entry_reports` with `status="failed"` and a non-empty `error`:

```json
{
  "status": "completed",
  "entry_reports": [
    {
      "kb_entry_id": "bbbbbbbb-bbbb-4000-8000-bbbbbbbbbbbb",
      "status": "failed",
      "aggregate_scores": {},
      "question_results": [],
      "error": "Entry not found in vector store — has it been indexed?"
    }
  ]
}
```

## Errors

| Status | When |
|--------|------|
| 404 | `run_id` not found (never started, or AI service was restarted) |

## Polling guidance

Evaluation typically completes in 30–120 seconds depending on the number of entries, `max_contexts`, and LLM response times. Recommended polling interval: **5 seconds**.

```js
async function waitForResult(runId, intervalMs = 5000) {
  while (true) {
    const res = await fetch(`/ai/api/v1/retrieval-evaluation/${runId}`);
    const body = await res.json();
    if (body.status === "completed" || body.status === "failed") {
      return body;
    }
    await new Promise(r => setTimeout(r, intervalMs));
  }
}
```

## Code

- Endpoint: [ai/src/presentation/api/v1/retrieval_evaluation/endpoints/status.py](../../../../../ai/src/presentation/api/v1/retrieval_evaluation/endpoints/status.py)
- Run store: `ai/src/infrastructure/retrieval_evaluation/run_store.py`
