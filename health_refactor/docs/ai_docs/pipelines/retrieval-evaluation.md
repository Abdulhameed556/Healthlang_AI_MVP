# KB Retrieval Evaluation Pipeline

Measures **RAG quality** for a knowledge base: given an agent and a KB
document, it auto-generates test questions, runs them through the retrieval
pipeline, and scores how well retrieval (and a grounded answer) performed using
five DeepEval metrics.

This pipeline is **isolated from the chat pipeline** — it has its own minimal,
context-only answer generator so the metrics reflect retrieval quality, not
chat orchestration.

## Flow

```
agent_id + kb_entry_id
        │
        ▼
┌────────────────────────┐
│  LoadSourceChunksStep  │  S3 download → parse → chunk (reuses indexing stack)
└───────────┬────────────┘
            │ source_chunks
            ▼
┌────────────────────────┐
│  SynthesizeTestsetStep │  DeepEval Synthesizer → question + expected_answer goldens
└───────────┬────────────┘
            │ goldens
            ▼
┌────────────────────────┐   per golden:
│   RunTestCasesStep     │   retrieve(q, agent_id) → chunks
│                        │   generate answer from chunks (isolated)
│                        │   score with 5 metrics
└───────────┬────────────┘
            │ question_results
            ▼
   aggregate (mean per metric) → EvaluationReport
```

## Metrics (DeepEval)

| Metric | Evaluates | Needs golden answer |
|---|---|---|
| `ContextualRelevancy` | Are retrieved chunks relevant to the query? | no |
| `ContextualPrecision` | Are relevant chunks ranked above irrelevant ones? | yes |
| `ContextualRecall` | Does retrieval surface everything the answer needs? | yes |
| `Faithfulness` | Is the answer grounded in retrieved chunks (no hallucination)? | no |
| `AnswerRelevancy` | Does the answer address the question? | no |

Golden answers come from the synthesizer (`include_expected_output=True`), so
all five metrics are available out of the box. The judge model defaults to
`settings.default_judge_model`; threshold defaults to 0.7.

## API

```
POST /retrieval-evaluation/run
  body: { agent_id, kb_entry_id, top_k?, max_contexts?, max_goldens_per_context? }
  → 202 { run_id, status: "pending" }

GET /retrieval-evaluation/{run_id}
  → { run_id, status, aggregate_scores, question_results[...], error }
```

Runs execute in the background (FastAPI `BackgroundTasks`) and are polled via
the status endpoint. `status` ∈ `pending | running | completed | failed`.

## Run store

Results live in an in-memory `IEvaluationRunStore` (process-local) — sufficient
for single-process dev/demo. Swap for a Redis/DB-backed implementation behind
the same interface for production / multi-worker deployments.

## Layout

- Domain: [entities.py](../../../ai/src/domain/retrieval_evaluation/entities.py), [interfaces.py](../../../ai/src/domain/retrieval_evaluation/interfaces.py)
- Application: [pipeline.py](../../../ai/src/application/retrieval_evaluation/pipeline.py), `steps/`, [dependencies.py](../../../ai/src/application/retrieval_evaluation/dependencies.py)
- Infrastructure: `synthesizer.py`, `scorer.py`, `answer_generator.py`, `run_store.py`
- Presentation: [router.py](../../../ai/src/presentation/api/v1/retrieval_evaluation/router.py), `endpoints/run.py`, `endpoints/status.py`

## Not in scope

This evaluates **retrieval/RAG quality**. Conversational/agent evaluation
(simulated user ↔ agent, ConversationalGEval) is a separate concern that lives
with the chat pipeline.
