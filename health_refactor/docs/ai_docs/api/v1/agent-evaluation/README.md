# Agent Evaluation API

**Audience:** Frontend developers integrating the "Configure New Evaluation" UI.

The agent evaluation feature runs simulated multi-turn conversations against a deployed AI agent, then scores those conversations with an AI judge against the criteria you define. Results are persisted to S3 so they survive server restarts.

> For internal pipeline quality testing (guardrail accuracy, scenario routing, KB relevancy), see [`../chat-evaluation/README.md`](../chat-evaluation/README.md).

---

## Endpoints

| Method | Path | Doc | Purpose |
|--------|------|-----|---------|
| `POST` | `/ai/api/v1/chat-evaluation/runs` | [run.md](run.md) | Start a new evaluation run |
| `GET` | `/ai/api/v1/chat-evaluation/status/{run_id}` | [status.md](status.md) | Poll status and retrieve results |
| `GET` | `/ai/api/v1/chat-evaluation/runs` | [history.md](history.md) | List past runs for an agent (newest first) |

---

## How it works

```
POST /runs  →  { "run_id": "...", "status": "pending" }
                    │
                    └─ background: generates synthetic conversations
                                   runs each one through the live agent
                                   AI judge scores against your criteria
                                   saves full report to S3
                    │
GET /status/{run_id}  →  { "status": "completed", "case_results": [...] }
```

Poll every 2–3 seconds until `status` is `completed` or `failed`.

---

## UI field → API field mapping

| UI label | API field | Range / type | Notes |
|----------|-----------|--------------|-------|
| Agent Selection | `agent_id` | UUID | UUID of the deployed agent |
| First Speaker toggle | `first_speaker` | `"agent"` \| `"human_sim"` | Default `"human_sim"` |
| Welcome Message | `welcome_message` | string | Only sent when `first_speaker="agent"` |
| Max Steps | `conversation_rounds` | 2–10, default `5` | UI label differs from API field name |
| Max Minutes | `max_minutes` | 1–30, default `10` | — |
| Evaluation Criteria | `judge_criteria` | array of strings | Each entry is one rule for the AI judge |
| Agent Variables | `agent_variables` | `{ key: value }` | Injected into simulated customer persona |
| API Tool Mocks | `api_tool_mocks` | `{ tool_name: { ...json } }` | See "Pre-populating API Tool Mocks" in [run.md](run.md) |

### Loading the API Tool Mocks panel

The tool mock slots are not free-form — they must match the tools actually attached to the selected agent. Render them using this flow before showing the form:

1. `GET /api/v1/agents/{agent_id}` → extract `data.api_tool_ids[]`
2. `GET /api/v1/api-tools/?page=1&page_size=100` → get `name` for each tool (backend service, Bearer token required)
3. Filter to tools whose `api_tool_id` is in `api_tool_ids`
4. Render one mock slot per tool; show a warning badge for any slot left empty ("No mock response defined. This tool will fail if called.")

Full detail in [run.md — Pre-populating API Tool Mocks](run.md#pre-populating-api-tool-mocks-in-the-ui).

---

## What the UI should display

After the run completes, the primary results to surface are **judge scores per criterion**:

```json
"judge_scores": {
  "Agent greeted the customer using the configured opening verbiage.": {
    "score": 1.0,
    "reason": "Agent opened with 'Hi! I'm the Afriex support assistant...'"
  },
  "Agent responded based on the customer's actual remitted amount when relevant.": {
    "score": 0.8,
    "reason": "Amount referenced correctly in turn 2 but not in follow-up."
  }
}
```

Each criterion has a `score` (0–1) and a `reason` (one-line AI explanation). These live inside each `case_result` in the status response.

The `aggregate_scores.judge_score` is the mean of all per-criterion scores across all conversations — useful for a top-level pass/fail indicator.

---

## Status lifecycle

```
pending → running → completed
                  ↘ failed
```

`failed` runs include an `error` string explaining what went wrong.

---

## Related

- [run.md](run.md) — full request body reference
- [status.md](status.md) — full results response reference
- [history.md](history.md) — list endpoint
- [`../chat-evaluation/README.md`](../chat-evaluation/README.md) — internal pipeline eval (engineers/QA)
