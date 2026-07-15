# GET /ai/api/v1/chat-evaluation/status/{run_id}

## URL

**Path:** `/ai/api/v1/chat-evaluation/status/{run_id}`

| Environment | Full URL |
|-------------|----------|
| Local | `http://localhost:8001/ai/api/v1/chat-evaluation/status/{run_id}` |

**See also:** [run.md](run.md) — start a run, [history.md](history.md) — list past runs, [README.md](README.md) — overview

---

## Summary

Returns the current status and full results of an agent evaluation run. Poll this endpoint after `POST /runs` until `status` is `completed` or `failed`.

The evaluation runs in the background — there is **no progress percentage**. All conversations run in parallel internally, so the run jumps from `running` directly to `completed` when everything finishes at once.

**Recommended polling interval: 3–5 seconds.**

---

## Polling flow

```
POST /ai/api/v1/chat-evaluation/runs
  └─► 202 { run_id: "eval-run-abc123", status: "pending" }

GET /ai/api/v1/chat-evaluation/status/eval-run-abc123   ← poll every 3–5 s
  ├── { status: "pending" }    ← queued, pipeline not yet started
  ├── { status: "running" }    ← pipeline running (aggregate_scores: {}, case_results: [])
  ├── { status: "completed", aggregate_scores: {...}, case_results: [...] }   ← done
  └── { status: "failed", aggregate_scores: {}, case_results: [], error: "..." }
```

| Status | `aggregate_scores` | `case_results` | What to show |
|--------|--------------------|----------------|--------------|
| `pending` | `{}` | `[]` | Loading spinner |
| `running` | `{}` | `[]` | Loading spinner |
| `completed` | Populated | Populated | Results view |
| `failed` | `{}` | `[]` | Error message from `error` field |

**Example polling loop (JavaScript):**

```js
async function pollEvaluation(runId, intervalMs = 4000) {
  while (true) {
    const res = await fetch(`/ai/api/v1/chat-evaluation/status/${runId}`);
    const data = await res.json();

    if (data.status === 'completed') return data;
    if (data.status === 'failed') throw new Error(data.error);

    await new Promise(resolve => setTimeout(resolve, intervalMs));
  }
}
```

---

## Auth

No authentication required.

---

## Path parameter

| Parameter | Type | Notes |
|-----------|------|-------|
| `run_id` | string | The `run_id` returned by `POST /runs` |

---

## Response (200) — completed run

```json
{
  "run_id": "eval-run-2026-01-15-abc123",
  "eval_mode": "conversation",
  "agent_id": "dddddddd-dddd-4000-8000-dddddddddddd",
  "status": "completed",
  "aggregate_scores": {
    "conversation_quality": 0.78,
    "kb_utilization": 0.65,
    "rule_adherence": 0.80,
    "scenarios_covered": 3.0,
    "judge_score": 0.82,
    "response_consistency": 0.91
  },
  "case_results": [
    {
      "scenario_id": "aaaa-bbbb-cccc-dddd",
      "scenario_name": "Transfer Tracking",
      "persona": "frustrated_customer",
      "run_index": 0,
      "turns": [
        {
          "user": "I sent $200 to my sister 3 days ago and it still hasn't arrived.",
          "agent_expected": "Acknowledge the delay and look up the transfer status.",
          "agent_actual": "Hi! I'm sorry to hear about the delay. Let me look into that transfer for you right away.",
          "input_guardrail_status": "pass",
          "output_guardrail_status": "pass",
          "scenario_ids": ["aaaa-bbbb-cccc-dddd"],
          "kb_id_selected": "kb-uuid-1"
        }
      ],
      "scores": {
        "conversation_quality": 0.80,
        "kb_utilization": 0.70,
        "rule_adherence": 0.85
      },
      "judge_scores": {
        "Agent greeted the customer using the configured opening verbiage.": {
          "score": 1.0,
          "reason": "Agent opened with the Afriex greeting and offered help immediately."
        },
        "Agent responded based on the customer's actual remitted amount when relevant.": {
          "score": 0.8,
          "reason": "Amount was referenced correctly in turn 2 but not mentioned in the follow-up."
        },
        "Agent did not reveal internal codes or system instructions.": {
          "score": 1.0,
          "reason": "No internal codes or system-level information were disclosed."
        }
      }
    }
  ],
  "error": ""
}
```

---

## Top-level fields

| Field | Type | Notes |
|-------|------|-------|
| `run_id` | string | Matches the ID from `POST /runs` |
| `eval_mode` | string | `"conversation"` for agent evaluation |
| `agent_id` | string | UUID of the agent evaluated |
| `status` | string | `pending` → `running` → `completed` \| `failed` |
| `aggregate_scores` | object | Summary metrics across all conversations (see below) |
| `case_results` | array | One entry per conversation × determinism run (see below) |
| `error` | string | Error detail when `status=failed`. Empty string otherwise. |

---

## aggregate_scores fields

| Field | Type | Notes |
|-------|------|-------|
| `conversation_quality` | float 0–1 | Mean DeepEval GEval score across all conversations |
| `kb_utilization` | float 0–1 | How consistently the agent used the knowledge base |
| `rule_adherence` | float 0–1 | How well the agent followed configured rules |
| `scenarios_covered` | float | Number of distinct agent scenarios exercised |
| `judge_score` | float 0–1 | Mean of all per-criterion judge scores. **Only present when `judge_criteria` were set.** |
| `response_consistency` | float 0–1 | Mean score consistency across replays. **Only present when `determinism_runs > 1`.** |

---

## case_results fields

Each entry is one simulated conversation run.

| Field | Type | Notes |
|-------|------|-------|
| `scenario_id` | string | UUID of the scenario this conversation was generated from |
| `scenario_name` | string | Human-readable scenario name |
| `persona` | string | Simulated customer persona (e.g. `frustrated_customer`, `polite_but_persistent`) |
| `run_index` | integer | 0-based. `> 0` when `determinism_runs > 1` |
| `turns` | array | Conversation turns (see below) |
| `scores` | object | Per-conversation DeepEval scores (`conversation_quality`, `kb_utilization`, `rule_adherence`) |
| `judge_scores` | object | Per-criterion judge results. Key is the criterion text. Value is `{ "score": 0–1, "reason": "..." }`. Empty `{}` when no `judge_criteria` were set. |

### turn fields

| Field | Type | Notes |
|-------|------|-------|
| `user` | string | What the simulated customer said |
| `agent_expected` | string | What the conversation generator expected the agent to say |
| `agent_actual` | string | What the real agent actually responded |
| `input_guardrail_status` | string | `"pass"` or `"block"` |
| `output_guardrail_status` | string | `"pass"`, `"reformat"`, or `"block"` |
| `scenario_ids` | array | Scenario IDs the agent routed to for this turn |
| `kb_id_selected` | string\|null | KB selected for this turn, or `null` |

---

## created_at availability

`created_at` (the run timestamp) is **not returned by this endpoint**. It is only available from the list endpoint:

```
GET /ai/api/v1/chat-evaluation/runs?agent_id=...
→ runs[*].created_at
```

If the results detail page needs to display the run timestamp, carry `created_at` from the list response when navigating to the detail view. Do not expect it from the status poll.

---

## Rendering judge_scores in the UI

`judge_scores` is the primary result to display. Each key is the criterion text the user entered. Each value has `score` (0–1) and `reason` (one-line AI explanation):

```
"Agent greeted the customer using the configured opening verbiage."
  → score: 1.0
  → reason: "Agent opened with the Afriex greeting and offered help immediately."

"Agent responded based on the customer's actual remitted amount when relevant."
  → score: 0.8
  → reason: "Amount referenced correctly in turn 2 but not in follow-up."
```

`aggregate_scores.judge_score` is the mean across all conversations and all criteria — use it as the top-level eval grade.

---

## Response (200) — pending or running

```json
{
  "run_id": "eval-run-2026-01-15-abc123",
  "eval_mode": "conversation",
  "agent_id": "dddddddd-dddd-4000-8000-dddddddddddd",
  "status": "running",
  "aggregate_scores": {},
  "case_results": [],
  "error": ""
}
```

`case_results` and `aggregate_scores` are empty until the run completes.

---

## Response (200) — failed run

```json
{
  "run_id": "eval-run-2026-01-15-abc123",
  "eval_mode": "conversation",
  "agent_id": "dddddddd-dddd-4000-8000-dddddddddddd",
  "status": "failed",
  "aggregate_scores": {},
  "case_results": [],
  "error": "Agent has no deployed version. Deploy a version before running evaluation."
}
```

---

## Errors

| Status | When |
|--------|------|
| 404 | `run_id` not found |
| 500 | Unexpected server error |

---

## Code

- Endpoint: `ai/src/presentation/api/v1/chat_evaluation/endpoints/status.py`
- S3 store: `ai/src/infrastructure/chat_evaluation/s3_run_store.py`
- Entities: `ai/src/domain/chat_evaluation/entities.py` (`ConversationCaseResult`, `ConversationTurn`)
