# Chat pipeline — architecture

How a single chat message flows from the HTTP API through agent runtime, guardrails,
orchestration, and persistence.

**See also:** [overview.md](overview.md) · [../api/v1/chat/README.md](../api/v1/chat/README.md) ·
[../pipelines/chat_runtime.md](../pipelines/chat_runtime.md)

---

## High-level connection map

```
┌─────────────────┐     deploy      ┌──────────────────────────────┐
│ Product backend │ ──────────────► │ agent_versions snapshot      │
│ POST /agents/   │                 │ (brand, rules, scenarios,    │
│ PUT  /agents/   │                 │  api_tool_ids, KB ids)       │
│ POST …/deploy   │                 └──────────────┬───────────────┘
└────────┬────────┘                                │
         │ same Postgres                           │ load at runtime
         ▼                                         ▼
┌─────────────────┐   POST /chat/sessions   ┌──────────────────────────────┐
│ Demo UI / client│ ───────────────────────►│ ChatSessionStore (DB)        │
└────────┬────────┘                         │ chat_sessions + metadata     │
         │                                   └──────────────┬───────────────┘
         │ POST /chat/messages                              │
         ▼                                                  │
┌───────────────────────────────────────────────────────────┴───────────────┐
│ ChatPipeline.run (application/chat/pipeline.py)                           │
│  1. load session + history (optional Redis cache)                         │
│  2. load AgentRuntimeContext from deployed snapshot                       │
│  3. input guardrail                                                       │
│  4. resolve API tools                                                     │
│  5. scenario routing (ScenarioAgent)                                      │
│  6. build system prompt (brand + rules + tools + session facts)           │
│  7. LangGraph orchestration (LLM ↔ tools loop)                            │
│  8. output guardrail                                                      │
│  9. merge session_facts → persist turn                                    │
└───────────────────────────────────────────────────────────────────────────┘
```

The AI service is mounted on the **same FastAPI process** as the product backend
(`ai/src/presentation/bootstrap.py` → `register_ai_v1_routes`). Chat routes live at
`/api/v1/chat/*` alongside `/api/v1/agents/*`.

---

## Layer responsibilities

| Layer | Package | Chat responsibility |
|-------|---------|---------------------|
| Presentation | `ai/src/presentation/api/v1/chat/` | HTTP: create session, send message |
| Application | `ai/src/application/chat/` | `ChatPipeline`, session facts, routing helpers |
| Domain | `ai/src/domain/chat_system/v1/` | Orchestration types, conversation state enum |
| Infrastructure | `ai/src/infrastructure/chat_system/v1/` | LangGraph, prompts, guardrails, tools |
| Shared backend | `backend/src/infrastructure/agent_runtime/` | Deployed agent snapshot → `AgentRuntimeContext` |
| Persistence | `ai/src/infrastructure/chat_sessions/` | Sessions + conversation logs in Postgres |

---

## Session lifecycle

### 1. Create session — `POST /api/v1/chat/sessions`

**Code:** `ai/src/application/chat/create_session.py`

1. Load **deployed** agent runtime via `load_scenario_runtime_with_report(agent_id)`.
   - Uses `backend/src/infrastructure/agent_runtime/` (same DB as product API).
   - Fails with `AgentNotDeployedError` (409) if no live version.
2. Insert `chat_sessions` row with `agent_id`, `agent_version_id`, `organization_id`.
3. Store `metadata.mode` (demo UI sends `"test"`).
4. Initial `conversation_state` = `in_progress`.

Returns `session_id` — client must send this on every message.

### 2. Send message — `POST /api/v1/chat/messages`

**Code:** `ai/src/application/chat/pipeline.py` → `ChatPipeline.run`

Each call runs **one full turn** (not streaming in v1). Response is a single JSON body
with the agent reply and updated `conversation_state`.

---

## Pipeline steps (one turn)

| Step | What happens | Key code |
|------|----------------|----------|
| **Session load** | Load session + prior user/agent text from DB (or Redis cache) | `ChatSessionStore.load` |
| **Runtime load** | Read deployed snapshot: brand, personalization, rules, scenarios, tools | `load_scenario_runtime_with_report` |
| **Input guardrail** | Optional block/rewrite before orchestration | `apply_input_screening` |
| **Tool resolution** | Map `api_tool_ids` from snapshot to LangChain tools | `resolve_orchestration_tools` |
| Step | What happens | Key code |
|------|----------------|----------|
| **Scenario routing** | Pick one or more scenarios (+ KB, rules); includes live date/time from `brand_config.timezone` | `ScenarioAgent` → `scenario_ids[]` capped by `max_scenarios_per_turn` |
| **System prompt** | Brand identity, timezone (live datetime), tone, rules, tools, session facts | `build_system_prompt` → `prompt_templates/v1.py` |
| **Orchestration** | LangGraph: LLM → (tools → LLM)* until done | `compile_chat_graph` |
| **Output guardrail** | Optional rewrite/block of assistant text | `apply_output_screening` |
| **Session facts** | Merge orchestrator `session_facts` delta into session metadata | `session_facts.py` |
| **Persist** | Optimistic Redis cache warm, then Postgres write in background (`async_session_persist`) | `ChatSessionStore.warm_cache_for_turn` + `append_turn_to_database` |
| **Response** | HTTP returns after orchestration; `turn_complete` timing excludes background DB | `ChatPipeline.run` |

`timing_ms.total` on the message response reflects **time-to-reply** (through orchestration). Background `persist_turn` is logged separately with `async_persist=true`.

---

## Agent configuration → prompt

Configuration is **not** read from the agent draft at chat time. Only the **deployed
version snapshot** is used.

| Snapshot field | Used in prompt as |
|----------------|-------------------|
| `brand_config.company_name` | Company label |
| `brand_config.identity_name` | “Your name” + opening line (falls back to agent `name`) |
| `brand_config.timezone` | Current date/time line in **orchestrator** and **scenario routing** (computed live each turn; see [agents API timezone catalog](../../../../backend_docs/api/v1/agents/README.md#brand_configtimezone)) |
| `brand_config.prompt` | Brand voice instructions |
| `brand_config.languages` | Supported languages |
| `personalization_config.*` | Tone, formality, pacing, greeting/sign-off style |
| `rules[]` | Guardrails + orchestration rule list |
| `scenarios[]` | Scenario agent routing + optional scenario prompt block |
| `api_tool_ids[]` | Tools bound to the LLM for this turn |

**Code path:**

```
AgentVersion.configuration_snapshot
  → snapshot_to_runtime_context (backend agent_runtime/mappers.py)
  → AgentRuntimeContext
  → build_prompt_context (orchestration/prompt_context.py)
  → build_system_prompt (orchestration/prompt_templates/v1.py)
  → format_brand_identity / format_personalization (prompts/brand_voice.py)
```

After editing an agent in the dashboard, **re-deploy** before expecting chat changes.

---

## LangGraph orchestration loop

**Code:** `ai/src/infrastructure/chat_system/v1/orchestration/graph.py`

```
START → llm → (tool calls?) → tools → llm → … → END
```

- The LLM must reply with structured `<json>` containing `message`, `conversation_state`,
  and `session_facts` (see `OUTPUT_FORMAT` in `prompt_templates/v1.py`).
- Tool calls execute HTTP GETs against configured API tools (`tools/http.py`,
  `tools/executor.py`).
- Max LLM rounds per user message: `DEFAULT_CHAT_CONFIG.max_orchestration_llm_calls`
  (default 50).

---

## Conversation state

Orchestrator sets `conversation_state` each turn. Values match
`backend/src/domain/chat_sessions/value_objects.py`:

| Value | Meaning |
|-------|---------|
| `in_progress` | Normal active chat |
| `waiting_on_customer` | Agent asked a question; waiting for user |
| `pending_close` | Agent offered to end; grace period before auto-close — **planned** |
| `end_conversation` | Closure confirmed or timed out; session should close |
| `transfer_to_live_support` | Hand off to human support |

Persisted on the session and returned on every message response.

**Planned:** grace-period auto-close, closed-session guard on send-message, and post-close
ticketing — see [session-close-and-ticketing.md](session-close-and-ticketing.md).

**Closed sessions:** `POST /api/v1/chat/messages` will reject messages when
`chat_sessions.status = closed` and tell the client to start a new session (planned).

---

## Session facts (cross-turn memory)

Within a turn, tool results are visible to the LLM only in that turn’s graph state.
**Session facts** persist across turns in `chat_sessions.metadata.session_facts`.

- Orchestrator returns a **delta** in JSON `session_facts` each turn.
- Pipeline merges by key and injects known facts into the system prompt.
- **Code:** `ai/src/application/chat/session_facts.py`

---

## Guardrails

| Guardrail | Default | Purpose |
|-----------|---------|---------|
| Input | on | Block unsafe user input before orchestration |
| Output | off | Screen assistant reply before delivery |
| Scenario | on | Route to scenario + KB before main agent |

Toggle defaults in `ai/src/application/chat/settings.py` (`DEFAULT_CHAT_CONFIG`).

---

## Data stores

| Store | Contents |
|-------|----------|
| Postgres `chat_sessions` | Session row, `conversation_state`, `metadata` (mode, session_facts) |
| Postgres `conversation_logs` | User/agent message text + turn metadata |
| Postgres `agents` / `agent_versions` | Draft + deployed snapshots |
| Redis (optional) | Session history cache when `use_session_cache=true` |

---

## Configuration knobs

Edit deployment defaults in `ai/src/application/chat/settings.py`:

| Setting | Default | Effect |
|---------|---------|--------|
| `ENABLE_INPUT_GUARDRAIL` | `true` | Input screening |
| `ENABLE_OUTPUT_GUARDRAIL` | `false` | Output screening |
| `ENABLE_SCENARIO_ROUTING` | `true` | ScenarioAgent before orchestration |
| `USE_TEST_TOOLS` | `true` | Allow test tool bindings in dev |
| `USE_SESSION_CACHE` | `false` | Redis session cache |
| `MAX_HISTORY_MESSAGES` | `15` | History window passed to LLM |
| `MAX_ORCHESTRATION_LLM_CALLS` | `50` | Max LLM steps per message |
| `MAX_SCENARIOS_PER_TURN` | `2` | Max scenario ids routed per turn |

LLM provider/model: `ai/src/infrastructure/chat_system/v1/orchestration/config.py`
(`DEFAULT_CONFIG`).

---

## Related packages (quick index)

| Concern | Path |
|---------|------|
| HTTP endpoints | `ai/src/presentation/api/v1/chat/endpoints/` |
| Pipeline orchestration | `ai/src/application/chat/pipeline.py` |
| Create session use-case | `ai/src/application/chat/create_session.py` |
| System prompt v1 | `ai/src/infrastructure/chat_system/v1/orchestration/prompt_templates/v1.py` |
| Brand / timezone in prompt | `ai/src/infrastructure/chat_system/v1/prompts/brand_voice.py` |
| Scenario routing agent | `ai/src/infrastructure/chat_system/v1/agents/scenario_agent/` |
| Runtime loader | `ai/src/infrastructure/chat_system/v1/agents/scenario_agent/runtime_loader.py` |
| Agent deploy snapshot | `backend/src/infrastructure/agent_runtime/` |

---

## Not yet wired (TODOs in code)

- **Knowledge base retrieval:** scenario routing returns `knowledge_base_id` +
  `retrieval_query`, but RAG chunk injection into the orchestration prompt is still
  marked TODO in `pipeline.py`.
- **SSE streaming:** v1 chat returns one JSON response per message; streaming is planned
  for a future endpoint shape.
