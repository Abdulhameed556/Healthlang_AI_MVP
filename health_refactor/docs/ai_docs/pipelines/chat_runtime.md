# Chat Runtime Pipeline

End-to-end flow for `POST /api/v1/chat/messages`. For architecture diagrams and
package map, see **[../architecture/chat-pipeline.md](../architecture/chat-pipeline.md)**.

API reference: **[../api/v1/chat/README.md](../api/v1/chat/README.md)**

---

## Entry points

| HTTP | Application |
|------|-------------|
| `POST /api/v1/chat/sessions` | `create_chat_session()` |
| `POST /api/v1/chat/messages` | `ChatPipeline.run()` |

Both use the same deployed agent runtime loader:
`load_scenario_runtime_with_report(agent_id)`.

---

## One message turn (`ChatPipeline.run`)

| # | Step | Timing key | Notes |
|---|------|------------|-------|
| 1 | Load session + history | `session_load` | Postgres; optional Redis cache |
| 2 | Load agent runtime | `runtime_load` | Deployed snapshot only |
| 3 | Input guardrail | `input_guardrail` | May stop pipeline (`pipeline_stopped`) |
| 4 | Resolve API tools | — | From snapshot `api_tool_ids` |
| 5 | Scenario routing | `scenario_routing` | `ScenarioAgent` picks scenario/KB |
| 6 | Build system prompt | — | Brand, timezone, rules, facts, tools |
| 7 | LangGraph orchestration | `orchestration` | LLM ↔ tools loop |
| 8 | Output guardrail | `output_guardrail` | Optional rewrite |
| 9 | Merge session facts | — | Persist in session metadata |
| 10 | Persist turn | — | User + agent conversation logs |

Defaults: `ai/src/application/chat/settings.py` → `DEFAULT_CHAT_CONFIG`.

**Planned:** session close grace period, auto-close worker, closed-session guard on send-message,
and post-close ticketing — [../architecture/session-close-and-ticketing.md](../architecture/session-close-and-ticketing.md).

---

## System prompt contents

Built in `build_system_prompt()` → `orchestration/prompt_templates/v1.py`:

- Agent identity (`identity_name` or agent name) + company
- Brand voice prompt, timezone / current datetime
- Personalization (tone, formality, pacing, greeting style)
- Session conversation state + known session facts
- Active scenario prompt (if routed)
- Rules list
- Tool names + grounding policy
- JSON output format (`message`, `conversation_state`, `session_facts`)

Brand helpers: `ai/src/infrastructure/chat_system/v1/prompts/brand_voice.py`

---

## Orchestration graph

```
START → llm → [tools → llm → …] → END
```

- Compiled in `orchestration/graph.py`
- Parses `<json>` reply each LLM turn (`orchestration/response.py`)
- Executes GET API tools when the model requests them

---

## Session persistence

| Table / key | Content |
|-------------|---------|
| `chat_sessions.conversation_state` | Latest orchestrator state |
| `chat_sessions.metadata.session_facts` | Cross-turn fact memory |
| `chat_sessions.metadata.mode` | e.g. `test` |
| `conversation_logs` | User text + agent text + `turn_metadata` |

---

## Prerequisites

1. Agent **deployed** with live version.
2. Valid `session_id` from create session.
3. LLM credentials in environment.
4. Postgres up (shared with backend).

---

## Not implemented yet

- KB chunk retrieval into prompt (routing returns ids; RAG step is TODO in pipeline).
- SSE streaming for `/chat/messages` (current API returns one JSON body).
