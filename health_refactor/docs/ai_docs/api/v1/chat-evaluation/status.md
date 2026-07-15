# GET /ai/api/v1/chat-evaluation/status/{run_id}

## URL

**Path:** `/ai/api/v1/chat-evaluation/status/{run_id}`

| Environment | Example full URL |
|-------------|-----------------|
| Local | `http://localhost:8001/api/v1/chat-evaluation/status/3f7a12cd-...` |

**See also:** [run.md](run.md) — start a run, [README.md](README.md) — overview and metrics

## Summary

Returns the current status and full results of a chat evaluation run. Poll this endpoint after calling `POST /runs` until `status` is `completed` or `failed`.

Recommended polling interval: **2.5 seconds**.

## Auth

No authentication required.

## Path parameter

| Parameter | Type | Notes |
|-----------|------|-------|
| `run_id` | string | The `run_id` returned by `POST /runs` |

## Response (200)

```json
{
  "run_id": "3f7a12cd-...",
  "eval_mode": "input_guardrail",
  "agent_id": null,
  "status": "completed",
  "aggregate_scores": {
    "accuracy": 0.92,
    "false_positive_rate": 0.05,
    "false_negative_rate": 0.08
  },
  "case_results": [
    {
      "query": "Track my Afriex transfer",
      "expected_blocked": false,
      "actual_status": "pass",
      "correct": true,
      "attack_category": null,
      "blocked_reason": null
    }
  ],
  "error": ""
}
```

### Top-level fields

| Field | Notes |
|-------|-------|
| `run_id` | Matches the ID from `POST /runs` |
| `eval_mode` | Mode that was evaluated |
| `agent_id` | Agent used, or `null` for guardrail-only modes |
| `status` | `pending` → `running` → `completed` \| `failed` |
| `aggregate_scores` | Summary metrics for the whole run. Metrics vary by mode (see README). |
| `case_results` | Per-case objects. Schema varies by `eval_mode`. |
| `error` | Error detail when `status=failed`. Empty string otherwise. |

### `case_results` schema by mode

**`input_guardrail`**
```json
{
  "query": "...",
  "expected_blocked": true,
  "actual_status": "block",
  "correct": true,
  "attack_category": "persona_hijack",
  "blocked_reason": "Jailbreak attempt detected."
}
```

**`scenario`**
```json
{
  "query": "...",
  "scenario_correct": true,
  "actual_scenario_ids": ["uuid-1"],
  "expected_scenario_ids": ["uuid-1"],
  "kb_relevancy_score": 0.84,
  "kb_id_selected": "uuid-kb",
  "reason": "User is asking about transfer tracking..."
}
```
> `kb_relevancy_score` is `null` when no KB was selected or retrieval failed.

**`output_guardrail`**
```json
{
  "query": "...",
  "expected_action": "block",
  "actual_status": "block",
  "correct": true,
  "violation_category": "pii_exposure",
  "blocked_reason": "Response contained account number."
}
```

**`e2e`**
```json
{
  "query": "...",
  "expected_answer": "...",
  "actual_response": "...",
  "input_guardrail_status": "pass",
  "scenario_ids": ["uuid-1"],
  "kb_id_selected": "uuid-kb",
  "chunks_retrieved": 4,
  "output_guardrail_status": "pass",
  "pipeline_stopped": null,
  "metrics": [
    {
      "name": "answer_relevancy",
      "score": 0.91,
      "threshold": 0.7,
      "success": true,
      "reason": "The response directly addresses the user's question."
    },
    {
      "name": "faithfulness",
      "score": 0.88,
      "threshold": 0.7,
      "success": true,
      "reason": "All claims are grounded in the retrieved context."
    }
  ]
}
```
> `pipeline_stopped` is set to `"input_guardrail_block"` when the input guardrail stopped execution.

## Errors

| Status | When |
|--------|------|
| 404 | `run_id` not found (run never started, or service restarted) |
| 500 | Unexpected server error |

## Code

- Endpoint: [ai/src/presentation/api/v1/chat_evaluation/endpoints/status.py](../../../../../ai/src/presentation/api/v1/chat_evaluation/endpoints/status.py)
- Run store: `ai/src/infrastructure/chat_evaluation/run_store.py`
