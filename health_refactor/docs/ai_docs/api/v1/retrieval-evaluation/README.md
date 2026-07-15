# Retrieval Evaluation API (`/ai/api/v1/retrieval-evaluation`)

A developer/ops tool for measuring how well an agent's retrieval pipeline performs on a set of knowledge base documents. Uses [DeepEval](https://docs.confident-ai.com/) RAG metrics to score retrieval quality.

> **Internal / admin use.** This API is intended for engineers and QA teams, not end-users. There is no user-facing UI requirement in v1.

## How it works

```
POST /run  →  background batch starts  →  returns run_id
              ↓
    For each KB entry in parallel:
      1. Load source chunks from the document
      2. Synthesize N test questions (LLM)
      3. Retrieve context via the agent's retrieval chain
      4. Score with DeepEval RAG metrics
              ↓
GET /status/{run_id}  →  poll until status = completed | failed
```

## Status progression

```
pending → running → completed
                  → failed
```

| Status | Meaning |
|--------|---------|
| `pending` | Run is queued, background task not yet started |
| `running` | Evaluation is actively executing |
| `completed` | All (or some) entries evaluated successfully |
| `failed` | Every entry in the batch failed |

Individual entries within a batch can fail independently. The batch status is `failed` only when **all** entries fail. If some entries succeed and others fail, the batch is `completed` and the failed entries appear in `entry_reports` with `status=failed` and an `error` message.

## Metrics

| Metric | What it measures |
|--------|-----------------|
| `contextual_relevancy` | Are the retrieved chunks relevant to the question? |
| `contextual_precision` | Are the relevant chunks ranked highly (not buried)? |
| `contextual_recall` | Does the retrieved context cover the expected answer? |

All scores are between 0 and 1. Higher is better. Default threshold is 0.7 for each metric.

## Run store

Evaluation results are stored in an **in-memory run store** (not in the database). This means:

- Results are lost on AI service restart.
- There is no persistent history of past runs.
- Run IDs are valid only for the lifetime of the current process.

This is intentional for v1 — these are ad-hoc quality checks, not audit records.

## Endpoints

| Method | Path | Doc | Description |
|--------|------|-----|-------------|
| POST | `/ai/api/v1/retrieval-evaluation/run` | [run.md](run.md) | Start a batch evaluation run |
| GET | `/ai/api/v1/retrieval-evaluation/{run_id}` | [status.md](status.md) | Poll run status and retrieve results |

## Typical usage

```bash
# 1. Start a run
curl -X POST http://localhost:8001/ai/api/v1/retrieval-evaluation/run \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "dddddddd-dddd-4000-8000-dddddddddddd",
    "kb_entry_ids": ["aaaaaaaa-aaaa-4000-8000-aaaaaaaaaaaa"],
    "top_k": 5,
    "max_contexts": 4,
    "max_goldens_per_context": 2
  }'
# → { "run_id": "eval-2025-01-15-abc123", "status": "pending" }

# 2. Poll until done
curl http://localhost:8001/ai/api/v1/retrieval-evaluation/eval-2025-01-15-abc123
# → { "status": "completed", "aggregate_scores": { ... }, "entry_reports": [...] }
```

## Related

- [../../../pipelines/retrieval-evaluation.md](../../../pipelines/retrieval-evaluation.md) — pipeline internals
- [../../../../backend_docs/api/v1/knowledge_bases/README.md](../../../../backend_docs/api/v1/knowledge_bases/README.md) — managing KB entries
