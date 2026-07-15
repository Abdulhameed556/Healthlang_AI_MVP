# AI Service — Architecture Overview

The AI package (`ai/src/`) runs **inside the same FastAPI process** as the product
backend. Routes register under `/api/v1` via `ai/src/presentation/bootstrap.py`.

## Layers

| Layer | Package | Responsibility |
|-------|---------|----------------|
| Presentation | `ai/src/presentation/` | HTTP routes, error handlers, demo UI mount |
| Application | `ai/src/application/` | Pipelines: chat, indexing, evaluation, voice |
| Domain | `ai/src/domain/` | Types, interfaces, prompt contracts |
| Infrastructure | `ai/src/infrastructure/` | LLM SDKs, LangGraph, chat sessions, vector store |

Shared **agent configuration** (brand, rules, scenarios, tools) lives in the product
backend (`backend/src/`) and is loaded at chat runtime from **deployed version
snapshots**.

---

## How services connect

```
                    ┌─────────────────────────────────────┐
                    │  FastAPI (backend/src/main.py)      │
                    │  /api/v1/agents/*  ← product JWT    │
                    │  /api/v1/api-tools/*                │
                    │  /api/v1/chat/*    ← AI chat        │
                    │  /demo/            ← dev UI only     │
                    └──────────────┬──────────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
     ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
     │ Postgres       │  │ Redis (opt.)   │  │ LLM providers  │
     │ agents,        │  │ session cache  │  │ Gemini, etc.   │
     │ chat_sessions,  │  └────────────────┘  └────────────────┘
     │ conversation_  │
     │ logs, api_tools│
     └────────────────┘
```

**Configure agent** → product API writes draft to `agents`  
**Deploy agent** → snapshot in `agent_versions` (live runtime source)  
**Chat** → AI pipeline reads snapshot + session history → LLM → persist turn  

Deep dive: **[chat-pipeline.md](chat-pipeline.md)**

---

## Chat runtime (primary product path)

| Step | Endpoint / component |
|------|----------------------|
| Publish + Deploy | `POST /api/v1/agents/{id}/publish` then `POST /api/v1/agents/{id}/versions/{version_id}/deploy` (backend) |
| Start session | `POST /api/v1/chat/sessions` |
| Send message | `POST /api/v1/chat/messages` → `ChatPipeline` |

Pipeline doc: [../pipelines/chat_runtime.md](../pipelines/chat_runtime.md)  
API doc: [../api/v1/chat/README.md](../api/v1/chat/README.md)

---

## Other pipelines

| Pipeline | Trigger | Doc |
|----------|---------|-----|
| Indexing | Backend KB upload → internal route | [../pipelines/indexing.md](../pipelines/indexing.md) |
| Evaluation | Internal eval run | [../pipelines/evaluation.md](../pipelines/evaluation.md) |
| Voice | WebSocket `/api/v1/voice/stream` | [../pipelines/voice_runtime.md](../pipelines/voice_runtime.md) |

---

## Single-task LLM agent

One-shot LLM calls (no conversation loop): plain text, streaming, or structured JSON
via `<json>` tags. Used for guardrails, scenario routing, extraction.

See **[single_task_agent.md](../single_task_agent.md)**.

Key packages: `ai/src/domain/llm/`, `ai/src/infrastructure/llm/providers/`,
`ai/src/application/single_task_agent/`.

---

## Documentation map

| Topic | Path |
|-------|------|
| Chat pipeline architecture | [architecture/chat-pipeline.md](chat-pipeline.md) |
| Chat HTTP API | [api/v1/chat/README.md](../api/v1/chat/README.md) |
| All AI routes (quick ref) | [api/endpoints.md](../api/endpoints.md) |
| Git workflow | [git-workflow.md](../git-workflow.md) |
