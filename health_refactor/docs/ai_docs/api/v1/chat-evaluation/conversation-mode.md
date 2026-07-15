# Conversation Eval Mode

Deep dive into the `conversation` eval mode — how synthetic conversations are generated, replayed, and scored.

**See also:** [README.md](README.md) — overview, [run.md](run.md) — API reference, [testing.md](testin,..
g.md) — Swagger walkthrough

---

## Purpose

The `conversation` mode evaluates how well the agent handles realistic multi-turn customer interactions. Unlike `e2e` (which scores individual Q&A pairs) or `scenario` (which checks routing accuracy), `conversation` mode tests:

- Does the agent stay coherent and helpful across a full conversation?
- Does it draw on the right KB knowledge within context?
- Does it follow all configured rules throughout — even under awkward follow-up questions?

---

## How it works

Two sources of conversations are supported via `conversation_source`:

### Source: `synthetic` (default)

```
POST /runs { eval_mode: "conversation", agent_id: "...", conversation_source: "synthetic" }
     │
     ▼
GenerateConversationsStep
     │   Reads: agent scenarios + KB descriptions + rules
     │   Calls: ConversationGeneratorAgent (Groq llama-3.3-70b-versatile)
     │   Produces: 2 synthetic conversations per scenario, each with a random persona
     │   Stored in: ctx.conversations
     │
     ▼
RunConversationCasesStep
     │   For each conversation × determinism_run:
     │     For each turn:
     │       → Input guardrail
     │       → Scenario routing (with accumulated message history)
     │       → KB retrieval
     │       → Orchestration (LangGraph)
     │       → Output guardrail
     │     Scores full conversation with ConversationScorer (DeepEval GEval)
     │   Appends ConversationCaseResult to ctx.results
     │
     ▼
aggregate_scores
{
  "conversation_quality": 0.82,
  "kb_utilization": 0.74,
  "rule_adherence": 0.91,
  "scenarios_covered": 3.0
}
```

### Source: `real`

```
POST /runs { eval_mode: "conversation", agent_id: "...",
             conversation_source: "real", sample_size: 20 }
     │
     ▼
LoadRealConversationsStep
     │   Queries: chat_sessions WHERE agent_id=... ORDER BY started_at DESC LIMIT sample_size
     │   For each session: loads conversation_logs, filters speaker=="user"
     │   Skips: sessions with no user turns
     │   Stored in: ctx.conversations (same structure as synthetic)
     │
     ▼
RunConversationCasesStep
```

**When to use:** When the agent has production chat history and you want to evaluate against real customer interactions. Falls back gracefully to empty results if no sessions exist yet.

---

## Step 1: GenerateConversationsStep (synthetic source only)

**Source:** `ai/src/application/chat_evaluation/steps/generate_conversations.py`

Loads the agent runtime and generates conversations for each scenario (capped at 5 scenarios per run to stay within LLM rate limits).

For each scenario, two personas are randomly sampled from the pool of five:

| Persona | Behaviour |
|---------|-----------|
| `frustrated_customer` | Impatient, short sentences, expressing frustration |
| `confused_first_timer` | Asks basic questions, needs step-by-step guidance |
| `polite_but_persistent` | Courteous but follows up with detailed questions |
| `skeptical_user` | Questions everything — fees, policies, timelines |
| `calm_detailed` | Methodical, thorough, well-structured questions |

The `ConversationGeneratorAgent` receives:
- Scenario name, description, and configured agent prompt
- Knowledge base names and descriptions
- All agent rules
- The two persona names

It produces a JSON structure with 2 conversations, each containing 3–5 turns of `{user, agent_expected}` pairs. The `agent_expected` field is the generator's best-guess ideal response — it is **not** used for scoring, only as a reference. The actual agent response is what gets evaluated.

### Conversation structure stored in ctx.conversations

```python
{
    "scenario_id": "scn-abc123",
    "scenario_name": "Transfer Issues",
    "persona": "frustrated_customer",
    "turns": [
        {"user": "My transfer has been stuck for 3 days!", "agent_expected": "I'm sorry..."},
        {"user": "What can you do about it?", "agent_expected": "I can escalate..."},
    ]
}
```

---

## Step 2: RunConversationCasesStep

**Source:** `ai/src/application/chat_evaluation/steps/run_conversation_cases.py`

For each generated conversation, for each `determinism_run` index:

### Turn execution

Each user message is passed through the full production pipeline in sequence:

1. **Input guardrail** (`apply_input_screening`) — if blocked, the turn records `[blocked by input guardrail]` as `agent_actual` and continues to the next turn (does not abort the conversation).

2. **Scenario routing** (`ScenarioAgent.run()`) — called with the accumulated `message_history` as a tuple of `ChatMessage` objects. Message history grows with each completed turn, so the routing agent gains conversation context.

3. **KB retrieval** (`RetrievalPipeline.retrieve()`) — only triggered if the scenario agent selected a KB and produced a `retrieval_query`.

4. **Orchestration** (`compile_chat_graph` + `graph.ainvoke()`) — the LangGraph receives the full message history via `build_initial_state(message_history=...)`. If `api_tool_mocks` is set, the graph is compiled with mock-bound tool wrappers so the agent can call tools (returning canned responses instead of live HTTP). If `api_tool_mocks` is empty and the deployed agent has no API tools, the graph runs without tools. The agent's configured tool names are passed to `build_system_prompt` so the system prompt accurately describes which tools are available.

5. **Output guardrail** (`apply_output_screening`) — the `message_to_user` from the screener becomes `agent_actual`.

### Message history accumulation

After each turn:
```python
message_history.append(ChatMessage(role=MessageRole.USER, content=user_msg))
message_history.append(ChatMessage(role=MessageRole.ASSISTANT, content=final_message))
```

This history is passed to both the scenario agent and the orchestrator on subsequent turns — making the conversation coherent across turns.

### Determinism runs

If `determinism_runs > 1`, the same conversation is replayed that many times independently. Results are recorded as separate `ConversationCaseResult` objects with `run_index=0`, `run_index=1`, etc. The aggregate scores are averaged across all runs and all conversations — high variance in `conversation_quality` across run indices indicates non-deterministic agent behaviour.

When multiple runs are present, the aggregate also includes a `response_consistency` score: `1.0 - mean(score_range_across_runs_per_conversation)`. A score of `1.0` means the agent produced identical metric scores on every replay; lower values indicate drift between runs.

### Conversation rounds

`conversation_rounds` controls how many turns each synthetic conversation has. The default is `5`. Valid range is 2–10. This is passed directly to the conversation generator prompt — the LLM is instructed to produce exactly that many turns per conversation. Only applies to `conversation_source="synthetic"`.

---

## Step 3: ScoreWithJudgeStep

**Source:** `ai/src/application/chat_evaluation/steps/score_with_judge.py`

Runs only when `judge_criteria` is non-empty. Skips silently otherwise — no extra cost for runs that don't use it.

For each `ConversationCaseResult` produced by `RunConversationCasesStep`:

1. Formats all turns into a numbered transcript:
   ```
   Turn 1
     Customer: <user message>
     Agent: <agent_actual>
   Turn 2
     ...
   ```
2. Sends transcript + criteria list to `JudgeCriteriaAgent` (OpenAI `gpt-4o-mini`, temperature=0).
3. Receives one `{criterion, score, reason}` object per criterion.
4. Stores results in `ConversationCaseResult.judge_scores` as `{criterion_text: {score, reason}}`.

On LLM error or parse failure the `judge_scores` dict stays empty and the pipeline continues — a single failing judge call never aborts the evaluation.

**Source:** `ai/src/infrastructure/chat_system/v1/agents/judge_criteria/`

### Aggregate impact

When any results carry judge scores, `_aggregate_conversation()` adds `"judge_score"` to the run's `aggregate_scores`: the mean of all per-criterion `score` values across all results. Individual criterion breakdowns (score + reason) remain on each `case_results[].judge_scores` entry — this is the primary data the frontend displays to the user.

---

## Scoring: ConversationScorer

**Source:** `ai/src/infrastructure/chat_evaluation/conversation_scorer.py`

After all turns complete, the full conversation is scored using DeepEval `GEval`. Three metrics are evaluated:

| Metric | Criteria | Evaluation params |
|--------|----------|-------------------|
| `conversation_quality` | Agent responds helpfully, coherently, and on-topic across all turns. Resolves the customer's issue clearly and concisely. | input, actual_output |
| `kb_utilization` | Agent references relevant KB knowledge accurately where appropriate. Does not give vague generic answers when specific product info is available. | input, actual_output, context (KB descriptions) |
| `rule_adherence` | Agent follows all configured rules throughout. No PII exposure, stays in scope, applies policies correctly. | input, actual_output, context (rules) |

**Input to GEval:**
- `input` = scenario description (what the conversation is about)
- `actual_output` = full conversation formatted as:
  ```
  Turn 1
    Customer: <user message>
    Agent: <agent_actual response>
  Turn 2
    ...
  ```
- `context` = list of KB descriptions and rules

**Threshold:** 0.5 (lower than e2e because conversational quality scoring is more subjective).

---

## Aggregate scores

`_aggregate_conversation()` in `pipeline.py`:

| Score | Computation |
|-------|-------------|
| `conversation_quality` | Mean across all `ConversationCaseResult.scores["conversation_quality"]` |
| `kb_utilization` | Mean across all results |
| `rule_adherence` | Mean across all results |
| `scenarios_covered` | Count of distinct `scenario_id` values across all results (float for JSON compatibility) |
| `judge_score` | Mean of all per-criterion judge scores across all results. Only present when `judge_criteria` were provided and at least one result was scored. |

---

## Case result shape

Each `ConversationCaseResult` (in `case_results[]`) looks like:

```json
{
  "scenario_id": "scn-abc123",
  "scenario_name": "Transfer Issues",
  "persona": "frustrated_customer",
  "run_index": 0,
  "scores": {
    "conversation_quality": 0.82,
    "kb_utilization": 0.74,
    "rule_adherence": 0.91
  },
  "judge_scores": {
    "Agent accurately identified the customer's subscription tier before offering discounts.": {
      "score": 0.9,
      "reason": "Agent confirmed tier in turn 1 before recommending any plan."
    },
    "Tone remained professional and empathetic throughout the interaction.": {
      "score": 0.85,
      "reason": "Tone was consistently polite; minor abruptness in turn 3."
    }
  },
  "turns": [
    {
      "user": "My transfer has been stuck for 3 days!",
      "agent_expected": "I'm sorry to hear that...",
      "agent_actual": "I understand your frustration. Let me check your transfer status.",
      "input_guardrail_status": "pass",
      "output_guardrail_status": "pass",
      "scenario_ids": ["transfer_issue"],
      "kb_id_selected": "afriex-faq-kb"
    },
    {
      "user": "What can you do about it?",
      "agent_expected": "I can escalate this...",
      "agent_actual": "I'll escalate this to our transfers team immediately.",
      "input_guardrail_status": "pass",
      "output_guardrail_status": "pass",
      "scenario_ids": ["transfer_issue"],
      "kb_id_selected": "afriex-faq-kb"
    }
  ]
}
```

---

## Agents involved

### ConversationGeneratorAgent

| Property | Value |
|----------|-------|
| Source | `ai/src/infrastructure/chat_system/v1/agents/conversation_generator/` |
| Primary provider | Groq `llama-3.3-70b-versatile` |
| Fallback provider | OpenAI `gpt-4o-mini` |
| Temperature | 0.7 (creative variation between conversations) |
| Max tokens | 4096 (long output for full conversation JSON) |
| Prompt version | v1 |

The generator uses a structured JSON output format. If parsing fails, the scenario is skipped silently.

---

## Evaluation setup UI fields

These fields map directly to the admin UI's "New Evaluation Setup" form. All are optional and specific to `conversation` mode.

---

### `first_speaker` and `welcome_message`

Controls who sends the very first message in the simulated conversation.

| Value | Behaviour |
|-------|-----------|
| `"human_sim"` (default) | The simulated customer generates an opening message based on the scenario and persona. The `welcome_message` field is ignored. `message_history` starts empty. |
| `"agent"` | `message_history` is pre-seeded with `ChatMessage(role=ASSISTANT, content=welcome_message)` before the first user turn. The scenario routing agent and orchestrator both receive this pre-seeded history so subsequent turns are contextually aware of the agent's opening. |

**When to use `"agent"`:** When your deployed agent is configured to greet customers first (e.g. the chat widget always shows a "Hello, how can I help?" before the customer types anything). Using `"agent"` first accurately replicates the real customer experience.

**When to use `"human_sim"`:** When the customer always initiates. Produces slightly more varied opening turns.

---

### `agent_variables`

A key/value map of fake but realistic facts about the simulated customer for this test run.

```json
"agent_variables": {
  "customer_id": "cus_90812734",
  "support_tier": "Enterprise Gold",
  "account_status": "active"
}
```

**What it does:** These variables are injected into the `ConversationGeneratorAgent`'s system prompt so the LLM-generated customer turns naturally reference them — e.g. the simulated customer might say *"I'm on the Enterprise Gold plan and I need help with..."* rather than talking about a generic account.

**Why it matters:** Without variables, the synthetic customer has no specific context. With them, the conversation tests whether the agent correctly handles a customer with those specific attributes (tier, account state, etc.), without needing to connect to a real CRM or database.

**Scope:** Variables are available to the generator step only. They do not override session context or modify the deployed agent's runtime in any way.

---

### `api_tool_mocks`

A map of `tool_name → mock JSON response` that intercepts the agent's real API tool calls during evaluation.

```json
"api_tool_mocks": {
  "stripe_payments": {
    "status": "success",
    "balance": 450.00,
    "currency": "USD"
  },
  "get_customer_context": {
    "name": "Jane Doe",
    "tier": "Enterprise Gold",
    "open_tickets": 2
  }
}
```

**What it does:** When the agent's orchestration graph attempts to call a configured API tool (e.g. `stripe_payments`), the evaluation pipeline intercepts that call and returns your canned JSON instead of making a real HTTP request to the tool's `endpoint_url`.

**Why it matters:**
- Prevents real API calls (no Stripe charges, no Salesforce records, no rate-limit usage) during test runs
- Makes evaluation results reproducible — the same mock response is returned every time, so score variance reflects the agent's behaviour, not external data drift
- Lets you test specific data scenarios (e.g. a customer with a zero balance, or an expired subscription) without needing that state to exist in production

**Warning state:** If the agent attempts to call a tool whose name is **not** present in `api_tool_mocks`, the tool returns an error result: `"No mock defined for tool '...'"`. This is intentional — it surfaces cases where the agent called a tool you forgot to mock, which is a useful signal. Either add a mock for it, or investigate whether the agent should have called that tool at all in this scenario.

**Relationship to deployed tools:** The mock map is keyed by `tool.name` (the string name you gave the tool when you created it — e.g. `"get_customer_context"`, not the UUID). Only tools actually attached to the agent's deployed version can be called; mocks for non-attached tool names are silently ignored.

---

### `judge_criteria`

A list of free-text evaluation rules that the AI judge scores the finished conversation against.

```json
"judge_criteria": [
  "Agent accurately identified the customer's subscription tier before offering discounts.",
  "Tone remained professional and empathetic throughout the interaction.",
  "Agent did not ask for information it already had from context."
]
```

**What it does:** After `RunConversationCasesStep` finishes producing the transcript, `ScoreWithJudgeStep` passes the full conversation (all turns) and these criteria to a judge LLM. Each criterion is scored independently on a 0–1 scale with a reasoning note. Results are stored in `judge_scores` on each `ConversationCaseResult` and averaged into the run's `aggregate_scores`.

**How to write good criteria:**
- Be specific and observable: *"Agent asked for the customer's transfer ID before looking it up"* is better than *"Agent was helpful"*
- One criterion per rule — don't combine two checks into one sentence
- Write in past tense from the perspective of reviewing a completed conversation: *"Agent identified..."* not *"Agent should identify..."*

**Relationship to agent rules:** `judge_criteria` are separate from the agent's configured `rules`. Agent rules govern what the agent does during the conversation; judge criteria are retrospective checks used only during scoring.

---

### `max_minutes`

Maximum wall-clock time (in minutes, 1–30) the evaluation run is allowed to run before being aborted. Default `10`.

Used as a safety bound for long-running evaluations with many scenarios, high `determinism_runs`, or slow LLM providers. When the limit is reached, the run is marked `failed` with an error message indicating timeout.

---

## Limitations and known constraints

| Constraint | Detail |
|-----------|--------|
| Scenarios capped at 5 | Avoids Groq TPM/TPD rate limits during generation |
| `agent_expected` not scored | Only `agent_actual` (real pipeline output) is evaluated by GEval |
| GEval is LLM-based | Scores vary slightly between runs even with temperature=0 in the judge |
| S3 persistence | Full run reports and metadata are persisted to S3 — survives restarts. Generated conversations (`ctx.conversations`) are in-memory only during the run. |
| `determinism_runs=1` default | Meaningful determinism comparison requires ≥ 3 runs; higher values cost more LLM calls |

---

## Related

- [pipelines/chat-evaluation.md](../../../../pipelines/chat-evaluation.md) — pipeline internals
- [testing.md](testing.md) — Swagger walkthrough with example bodies
- [run.md](run.md) — API reference for POST /runs
