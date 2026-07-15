# POST /ai/api/v1/retrieval-evaluation/run

## URL

**Path:** `/ai/api/v1/retrieval-evaluation/run`

| Environment | Example full URL |
|-------------|-----------------|
| Local | `http://localhost:8001/ai/api/v1/retrieval-evaluation/run` |
| Staging | `https://ai.staging.afriex.io/ai/api/v1/retrieval-evaluation/run` |
| Production | `https://ai.afriex.io/ai/api/v1/retrieval-evaluation/run` |

**See also:** [status.md](status.md) — poll results, [README.md](README.md) — overview and metric descriptions

## Summary

Queues a batch retrieval-evaluation run for one or more KB entries. The call returns **immediately** with a `run_id` and `status=pending` — evaluation runs in the background.

For each KB entry, the pipeline:
1. Loads source document chunks.
2. Synthesises test question/answer pairs via LLM.
3. Retrieves context using the specified agent's retrieval chain.
4. Scores each result with DeepEval RAG metrics (`contextual_relevancy`, `contextual_precision`, `contextual_recall`).

Poll `GET /ai/api/v1/retrieval-evaluation/{run_id}` to check progress and retrieve results.

## Auth

No JWT required. The AI service uses an `INTERNAL_API_KEY` header for internal routes, but this endpoint is exposed on the product API without auth in v1.

## Request body

```json
{
  "agent_id": "dddddddd-dddd-4000-8000-dddddddddddd",
  "kb_entry_ids": [
    "aaaaaaaa-aaaa-4000-8000-aaaaaaaaaaaa",
    "bbbbbbbb-bbbb-4000-8000-bbbbbbbbbbbb"
  ],
  "top_k": 5,
  "max_contexts": 4,
  "max_goldens_per_context": 2
}
```

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `agent_id` | UUID | Yes | — | The agent whose retrieval pipeline to evaluate. The agent must be deployed with a live version. |
| `kb_entry_ids` | UUID[] | Yes | — | 1–10 KB entry IDs to evaluate. Each entry runs in parallel. |
| `top_k` | integer | No | `5` | Chunks retrieved per question. Range: 1–20. Higher = more recall, less precision. |
| `max_contexts` | integer | No | `4` | Max document chunks to synthesise questions from. Range: 1–20. |
| `max_goldens_per_context` | integer | No | `2` | Max question/answer pairs generated per context chunk. Range: 1–10. |

### Choosing parameters

| Goal | Recommendation |
|------|---------------|
| Fast smoke test | `max_contexts=2`, `max_goldens_per_context=1`, `top_k=3` |
| Thorough quality check | `max_contexts=8`, `max_goldens_per_context=3`, `top_k=10` |
| Default (balanced) | Keep all defaults |

> **Cost note:** Each context × golden pair = 2 LLM calls (synthesis + scoring). With defaults: 4 × 2 × 3 metrics = ~24 LLM calls per entry.

## Success (202)

```json
{
  "run_id": "eval-2025-01-15-abc123",
  "status": "pending"
}
```

> Note: this endpoint does **not** wrap the response in the standard `{ message, status_code, error, data }` envelope. The response is the schema directly.

| Field | Notes |
|-------|-------|
| `run_id` | Unique identifier for this run. Store it to poll `GET /{run_id}`. |
| `status` | Always `"pending"` at creation time. |

## Errors

| Status | When |
|--------|------|
| 422 | Invalid request body (missing required fields, `kb_entry_ids` empty, values out of range) |
| 500 | Unexpected server error |

## Frontend / script notes

- Store the `run_id` immediately after this call. It is the only way to retrieve results.
- `run_id` is only valid for the lifetime of the AI service process — results are not persisted to the database.
- You can submit up to 10 entries per batch. For more than 10 entries, split into multiple runs.
- The batch returns 202 (Accepted) to signal that work is queued, not completed.

## Code

- Endpoint: [ai/src/presentation/api/v1/retrieval_evaluation/endpoints/run.py](../../../../../ai/src/presentation/api/v1/retrieval_evaluation/endpoints/run.py)
- Pipeline builder: `ai/src/application/retrieval_evaluation/dependencies.py`
- Run store: `ai/src/infrastructure/retrieval_evaluation/run_store.py`
