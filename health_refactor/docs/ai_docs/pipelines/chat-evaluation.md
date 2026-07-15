# Chat Evaluation Pipeline

Internal tool for measuring AI pipeline quality across all chat stages.
For the HTTP API reference, see **[../api/v1/chat-evaluation/README.md](../api/v1/chat-evaluation/README.md)**.

---

## Entry points

| HTTP | Notes |
|------|-------|
| `POST /api/v1/chat-evaluation/datasets` | Upload reusable test cases, get `dataset_id` |
| `POST /api/v1/chat-evaluation/runs` | Trigger a run — returns `run_id` immediately (202) |
| `GET  /api/v1/chat-evaluation/status/{run_id}` | Poll until `completed` or `failed` |

Runs execute in a **FastAPI `BackgroundTasks`** worker — the POST endpoint returns before evaluation starts.

---

## Eval modes

| Mode | What is tested | Agent ID needed |
|------|---------------|----------------|
| `input_guardrail` | Attack / jailbreak blocking accuracy | No |
| `output_guardrail` | Pass / reformat / block action accuracy | No |
| `scenario` | Scenario routing + KB selection quality | Yes |
| `e2e` | All 4 stages in sequence + DeepEval answer quality | Yes |
| `conversation` | Auto-generated multi-turn conversations through real pipeline + GEval | Yes |

---

## Pipeline steps

The `ChatEvalPipeline` dispatches to one step class per mode. Only one step runs per evaluation run.

```
ChatEvalPipeline.run(ctx)
        │
        ├─ input_guardrail  ──► RunInputGuardrailCasesStep
        ├─ output_guardrail ──► RunOutputGuardrailCasesStep
        ├─ scenario         ──► RunScenarioCasesStep
        ├─ e2e              ──► RunE2eCasesStep
        └─ conversation     ──► GenerateConversationsStep
                                       │
                                RunConversationCasesStep
```

After all steps complete, `ChatEvalPipeline` computes `aggregate_scores` from `ctx.results` and writes a final `EvalReport` to the run store.

### `RunInputGuardrailCasesStep`

`ai/src/application/chat_evaluation/steps/run_input_guardrail_cases.py`

For each test case:
1. Calls `apply_input_screening(user_query, enabled=True)`
2. Determines correctness: `(actual_status == "block") == tc.should_block`
3. Appends a `GuardrailCaseResult` to `ctx.results`

Aggregate scores produced: `accuracy`, `false_positive_rate`, `false_negative_rate`.

### `RunScenarioCasesStep`

`ai/src/application/chat_evaluation/steps/run_scenario_cases.py`

For each test case:
1. Calls `ScenarioAgent().run(ScenarioAgentInput(agent_id, user_query))`
2. Compares `actual_scenario_ids` vs `tc.expected_scenario_ids` (set equality)
3. If the agent selected a KB and produced a retrieval query:
   - Calls `RetrievalPipeline.retrieve(query, agent_id)`
   - Scores chunks with `KBRelevancyScorer` (`ContextualRelevancyMetric`, threshold 0.7)
4. Appends a `ScenarioCaseResult` with `scenario_correct`, `kb_relevancy_score`, `reason`

KB relevancy is scored against retrieved chunks — **not** by UUID match — so the metric stays stable as KB content evolves.

Aggregate scores: `scenario_accuracy`, `kb_selection_rate`, `kb_relevancy_mean`.

### `RunOutputGuardrailCasesStep`

`ai/src/application/chat_evaluation/steps/run_output_guardrail_cases.py`

For each test case:
1. Calls `apply_output_screening(user_query, assistant_message, enabled=True)`
2. Determines correctness: `actual_status == tc.expected_action`
3. Appends a `GuardrailCaseResult` to `ctx.results`

Aggregate scores: `action_accuracy`.

### `RunE2eCasesStep`

`ai/src/application/chat_evaluation/steps/run_e2e_cases.py`

Loads the agent runtime once, compiles the LangGraph once (no tools — for eval isolation), then for each test case runs all stages in sequence:

| # | Stage | Notes |
|---|-------|-------|
| 1 | Input guardrail | `apply_input_screening` — if blocked, skips remaining stages, sets `pipeline_stopped` |
| 2 | Scenario routing | `ScenarioAgent().run()` → picks scenario + KB |
| 3 | KB retrieval | `RetrievalPipeline.retrieve()` — only if KB was selected |
| 4 | Orchestration | `build_system_prompt` + `build_initial_state` + `graph.ainvoke(state)` |
| 5 | Output guardrail | `apply_output_screening` on the LLM response |
| 6 | DeepEval scoring | `E2eScorer.score()` → `AnswerRelevancyMetric` + `FaithfulnessMetric` (threshold 0.7) |

**Isolation**: the LangGraph runs without API tools — prevents non-determinism from external calls and makes results reproducible across runs.

Aggregate scores: mean of `answer_relevancy` and `faithfulness` across all cases.

### `GenerateConversationsStep`

`ai/src/application/chat_evaluation/steps/generate_conversations.py`

Runs first in the `conversation` pipeline. For each agent scenario (up to 5):
1. Loads agent runtime via `load_scenario_runtime(agent_id)`
2. Randomly selects 2 personas from the 5 available: `frustrated_customer`, `confused_first_timer`, `polite_but_persistent`, `skeptical_user`, `calm_detailed`
3. Calls `ConversationGeneratorAgent.generate()` — a Groq-backed LLM agent that produces 2 synthetic conversations (3–5 turns each) following the persona style and scenario context
4. Appends each generated conversation to `ctx.conversations`

On generator failure, the scenario is skipped (not a hard error) and generation continues for remaining scenarios.

### `RunConversationCasesStep`

`ai/src/application/chat_evaluation/steps/run_conversation_cases.py`

For each conversation in `ctx.conversations`, and for each `determinism_run` in `range(ctx.determinism_runs)`:

Replays the conversation turn by turn through the full production pipeline:

| # | Stage | Notes |
|---|-------|-------|
| 1 | Input guardrail | `apply_input_screening` — blocked turns record `[blocked by input guardrail]` and continue to the next turn |
| 2 | Scenario routing | `ScenarioAgent.run()` with accumulated `message_history` — routing improves as conversation context builds |
| 3 | KB retrieval | `RetrievalPipeline.retrieve()` if KB was selected |
| 4 | Orchestration | Full LangGraph run with message history |
| 5 | Output guardrail | `apply_output_screening` on the LLM response |

Message history accumulates across turns using `ChatMessage(role, content)` — both user messages and agent responses are appended after each turn so the scenario agent has context for subsequent turns.

After all turns in a conversation complete, the full conversation is scored with `ConversationScorer` (DeepEval GEval). Appends a `ConversationCaseResult` per conversation × run to `ctx.results`.

Aggregate scores: mean of `conversation_quality`, `kb_utilization`, `rule_adherence` + `scenarios_covered` count.

---

## Shared context object

`ChatEvalContext` (`ai/src/application/chat_evaluation/context.py`) is the mutable bag passed to every step:

| Field | Purpose |
|-------|---------|
| `eval_mode` | Which step to dispatch to |
| `agent_id` | UUID string; `None` for guardrail-only modes |
| `test_cases` | Raw dict list from request or dataset store; empty list for `conversation` mode |
| `results` | List of `*CaseResult` dataclasses; appended by the step |
| `conversations` | List of generated conversation dicts; populated by `GenerateConversationsStep`, consumed by `RunConversationCasesStep` |
| `determinism_runs` | Integer (default 1); how many times each generated conversation is replayed |

---

## Infrastructure layer

| Class | Location | Notes |
|-------|----------|-------|
| `InMemoryRunStore` | `ai/src/infrastructure/chat_evaluation/run_store.py` | Singleton; results lost on restart |
| `InMemoryDatasetStore` | `ai/src/infrastructure/chat_evaluation/dataset_store.py` | Singleton; stores uploaded test case lists |
| `KBRelevancyScorer` | `ai/src/infrastructure/chat_evaluation/scorer.py` | Wraps `ContextualRelevancyMetric` via `asyncio.to_thread` |
| `E2EScorer` | `ai/src/infrastructure/chat_evaluation/scorer.py` | Wraps `AnswerRelevancyMetric` + `FaithfulnessMetric` via `asyncio.to_thread` |
| `ConversationScorer` | `ai/src/infrastructure/chat_evaluation/conversation_scorer.py` | Wraps 3 DeepEval `GEval` metrics via `asyncio.to_thread` |
| `ConversationGeneratorAgent` | `ai/src/infrastructure/chat_system/v1/agents/conversation_generator/` | Groq-backed agent; generates synthetic multi-turn conversations from scenario + persona |

DeepEval metrics run synchronously — `asyncio.to_thread` offloads them so they do not block the async event loop.

---

## Metrics reference

All scores are 0–1. DeepEval threshold: **0.7**.

| Mode | Aggregate metric | Per-case field |
|------|-----------------|----------------|
| `input_guardrail` | `accuracy`, `false_positive_rate`, `false_negative_rate` | `correct` |
| `output_guardrail` | `action_accuracy` | `correct` |
| `scenario` | `scenario_accuracy`, `kb_selection_rate`, `kb_relevancy_mean` | `scenario_correct`, `kb_relevancy_score` |
| `e2e` | `answer_relevancy`, `faithfulness` | `metrics[]` with `score`, `threshold`, `success`, `reason` |
| `conversation` | `conversation_quality`, `kb_utilization`, `rule_adherence`, `scenarios_covered` | `scores{}` dict, `turns[]` with per-turn guardrail statuses |

---

## Run lifecycle

```
POST /runs  →  RunStatus.PENDING
              │
              └─ BackgroundTasks worker starts
                    │
                    ├─ RunStatus.RUNNING
                    │
                    ├─ step runs all cases
                    │
                    ├─ aggregates computed
                    │
                    └─ RunStatus.COMPLETED  (or FAILED on exception)
```

Poll `GET /status/{run_id}` every 2.5 s. The run_id is only valid for the current server process lifetime (in-memory store).

---

## Prerequisites

1. Agent **deployed** with a live version (required for `scenario` and `e2e` modes).
2. Pinecone index populated (required for e2e KB retrieval).
3. OpenAI key in environment (required for DeepEval scoring and orchestration).
4. Postgres up (agent runtime loader reads from it).

---

## Code locations

| Layer | Path |
|-------|------|
| Domain entities | `ai/src/domain/chat_evaluation/entities.py` |
| Domain interfaces | `ai/src/domain/chat_evaluation/interfaces.py` |
| Application context | `ai/src/application/chat_evaluation/context.py` |
| Application pipeline | `ai/src/application/chat_evaluation/pipeline.py` |
| Application steps | `ai/src/application/chat_evaluation/steps/` |
| Infrastructure stores + scorers | `ai/src/infrastructure/chat_evaluation/` |
| API schemas | `ai/src/presentation/api/v1/chat_evaluation/schemas.py` |
| API endpoints | `ai/src/presentation/api/v1/chat_evaluation/endpoints/` |
| Unit tests | `tests/ai_tests/unit/application/chat_evaluation/` |
| API tests | `tests/ai_tests/unit/presentation/chat_evaluation/` |

---

## Related

- [chat_runtime.md](chat_runtime.md) — production chat pipeline that e2e mode exercises
- [retrieval-evaluation.md](retrieval-evaluation.md) — KB retrieval quality scoring (separate system)
- [../api/v1/chat-evaluation/README.md](../api/v1/chat-evaluation/README.md) — HTTP API reference
