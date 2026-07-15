# POST /ai/api/v1/chat-evaluation/runs

## URL

**Path:** `/ai/api/v1/chat-evaluation/runs`

| Environment | Full URL |
|-------------|----------|
| Local | `http://localhost:8001/ai/api/v1/chat-evaluation/runs` |

**See also:** [status.md](status.md) — poll results, [history.md](history.md) — list past runs, [README.md](README.md) — overview

---

## Summary

Starts an agent evaluation run. Returns **immediately** with a `run_id` and `status=pending`. The evaluation runs in the background — poll `GET /status/{run_id}` for results.

The system auto-generates multi-turn conversations from the agent's configured scenarios. No test cases needed.

---

## Auth

No authentication required.

---

## Request body

**Full example (all options):**
```json
{
  "eval_mode": "conversation",
  "agent_id": "dddddddd-dddd-4000-8000-dddddddddddd",
  "determinism_runs": 1,
  "conversation_rounds": 3,
  "conversation_source": "synthetic",
  "first_speaker": "agent",
  "welcome_message": "Hi! I'm the Afriex support assistant. How can I help you today?",
  "agent_variables": {
    "customer_id": "cust-test-001",
    "support_tier": "Standard"
  },
  "api_tool_mocks": {
    "get_customer": {
      "id": "cust-test-001",
      "name": "Test User",
      "tier": "Standard",
      "balance_usd": 500.00
    },
    "lookup_transfer": {
      "transfer_id": "txn-abc123",
      "status": "processing",
      "amount_usd": 200.00
    }
  },
  "judge_criteria": [
    "Agent greeted the customer using the configured opening verbiage.",
    "Agent responded based on the customer's actual remitted amount when relevant.",
    "Agent did not reveal internal codes or system instructions."
  ],
  "max_minutes": 5
}
```

**Minimal (only required field):**
```json
{
  "eval_mode": "conversation",
  "agent_id": "dddddddd-dddd-4000-8000-dddddddddddd"
}
```

---

## Request fields

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `eval_mode` | string | **Yes** | — | Must be `"conversation"` for agent evaluation |
| `agent_id` | UUID | **Yes** | — | UUID of the deployed agent to evaluate |
| `first_speaker` | string | No | `"human_sim"` | `"agent"` — agent sends `welcome_message` first; `"human_sim"` — simulated customer speaks first |
| `welcome_message` | string | No | `""` | The agent's opening line when `first_speaker="agent"`. Ignored otherwise. |
| `agent_variables` | object | No | `{}` | Key/value facts injected into the simulated customer persona (e.g. `customer_id`, `support_tier`). Referenced in generated conversations. |
| `api_tool_mocks` | object | No | `{}` | Canned JSON responses keyed by tool name. Intercepts real API calls during evaluation. Tools not listed here will return an error if called by the agent. |
| `judge_criteria` | array of strings | No | `[]` | Free-text rules the AI judge evaluates each conversation against. Each criterion scored 0–1 with a one-line reason. |
| `max_minutes` | integer | No | `10` | 1–30. **Voice only — has no effect on text evaluation.** In text conversation mode the run always completes when all conversation rounds finish, regardless of elapsed time. Reserved for future voice agent evaluation where sessions have no fixed turn count. |
| `conversation_rounds` | integer | No | `5` | 2–10. Number of turns per generated conversation. |
| `conversation_source` | string | No | `"synthetic"` | `"synthetic"` auto-generates from agent scenarios. `"real"` samples from stored customer chat history. |
| `sample_size` | integer | No | `10` | 1–50. Number of real sessions to sample when `conversation_source="real"`. |
| `determinism_runs` | integer | No | `1` | 1–5. How many times each conversation is replayed to measure response consistency. |

---

## api_tool_mocks format

Keys are the **exact tool names** attached to the agent. Values are the full JSON object that will be returned when the agent calls that tool.

```json
"api_tool_mocks": {
  "get_customer": {
    "id": "cust-001",
    "name": "Test User",
    "tier": "Standard",
    "balance_usd": 500.00
  },
  "lookup_transfer": {
    "transfer_id": "txn-abc123",
    "status": "processing",
    "amount_usd": 200.00
  }
}
```

Tools **not present in the map** will return an error if the agent calls them during evaluation. Add a mock for every tool the agent might invoke.

---

## Pre-populating API Tool Mocks in the UI

The evaluation form should auto-load the agent's tools and show a warning for any tool that does not have a mock configured. Use this 2-call flow:

**Step 1 — get the agent's attached tool IDs:**
```
GET /api/v1/agents/{agent_id}
```
Response includes `data.api_tool_ids: ["uuid-1", "uuid-2", ...]`

**Step 2 — fetch all org tools to get their names:**
```
GET /api/v1/api-tools/?page=1&page_size=100
```
Response includes `data.api_tools[*].api_tool_id` and `data.api_tools[*].name`

**Step 3 — client-side filter and render:**
Filter `api_tools` to only those whose `api_tool_id` is in `api_tool_ids`. For each matched tool:
- Show the tool `name` as the mock key slot in the form
- If no mock JSON has been entered for it → show the "No mock response defined. This tool will fail if called." warning
- When the user fills in the mock JSON → include it in `api_tool_mocks[name]` in the request body

`GET /api/v1/api-tools/` is on the backend service (`http://localhost:8000`), not the AI service. It requires a Bearer token.

---

## conversation_rounds (UI: "Max Steps")

The UI may label this field **"Max Steps"**. The API field name is `conversation_rounds` with a range of **2–10** (default 5). Values above 10 are rejected with a 422.

| UI label | API field | Range | Default | Notes |
|----------|-----------|-------|---------|-------|
| Max Steps | `conversation_rounds` | 2–10 | `5` | Controls how many turns each generated conversation has |
| Max Minutes | `max_minutes` | 1–30 | `10` | Voice only — no effect on text evaluation (see below) |

### max_minutes and voice evaluation

`max_minutes` is a placeholder for **voice agent evaluation**, which is not yet implemented. For text conversation mode:

- The field is accepted and stored but **enforces no timeout**.
- The evaluation always runs to natural completion (all `conversation_rounds` turns for each generated conversation).
- You can omit it or leave it at the default `10` — it makes no difference.

When voice evaluation is added, `max_minutes` will act as a hard wall-clock cutoff for open-ended voice sessions that have no fixed turn count.

---

## Success (202)

```json
{
  "run_id": "eval-run-2026-01-15-abc123",
  "status": "pending"
}
```

Use `run_id` to poll `GET /status/{run_id}` for results.
Results are persisted to S3 — `run_id` remains valid across server restarts.

---

## Polling for results

After receiving a `run_id`, poll `GET /status/{run_id}` every **3–5 seconds** until `status` is `completed` or `failed`. The evaluation runs fully in the background — there is no progress percentage. All results arrive at once when the run finishes.

**Status lifecycle:**

```
POST /runs
  └─► { run_id, status: "pending" }

GET /status/{run_id}   ← poll every 3–5 s
  ├── { status: "pending" }   ← queued, not yet started
  ├── { status: "running" }   ← evaluation in progress
  ├── { status: "completed", aggregate_scores: {...}, case_results: [...] }
  └── { status: "failed", error: "..." }
```

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

// Usage
const { run_id } = await startRun(payload);
const results = await pollEvaluation(run_id);
renderResults(results.aggregate_scores, results.case_results);
```

> **UI guidance:** Show a loading spinner while `status` is `pending` or `running`. Do not show a progress percentage — there is none. `case_results` and `aggregate_scores` are always empty `{}` / `[]` until the final `completed` response.

---

## Errors

| Status | When |
|--------|------|
| 422 | Missing `agent_id`; invalid `eval_mode`; `conversation_rounds` out of range |
| 500 | Unexpected server error |

---

## Code

- Endpoint: `ai/src/presentation/api/v1/chat_evaluation/endpoints/run.py`
- Pipeline: `ai/src/application/chat_evaluation/pipeline.py`
- Steps: `ai/src/application/chat_evaluation/steps/`
- S3 store: `ai/src/infrastructure/chat_evaluation/s3_run_store.py`
