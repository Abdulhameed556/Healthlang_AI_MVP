# AI Service API Endpoint Reference

All routes prefixed `/api/v1`. Mounted via `ai/src/presentation/bootstrap.py` on the
shared FastAPI app.

## Agent Evaluation (product feature — frontend integration)

Runs simulated multi-turn conversations against a deployed agent and scores results with an AI judge. Built for the "Configure New Evaluation" UI.

| Method | Path | Description | Doc |
|--------|------|-------------|-----|
| POST | `/ai/api/v1/chat-evaluation/runs` | Start a new evaluation run | [v1/agent-evaluation/run.md](v1/agent-evaluation/run.md) |
| GET | `/ai/api/v1/chat-evaluation/status/{run_id}` | Poll status and get full results | [v1/agent-evaluation/status.md](v1/agent-evaluation/status.md) |
| GET | `/ai/api/v1/chat-evaluation/runs` | List past runs for an agent | [v1/agent-evaluation/history.md](v1/agent-evaluation/history.md) |

Overview: [v1/agent-evaluation/README.md](v1/agent-evaluation/README.md)

## Internal Chat Pipeline Evaluation (ops/engineering)

Tests individual pipeline stages (guardrail, scenario routing, KB, e2e) using hand-crafted test cases. Not user-facing.

| Method | Path | Description | Doc |
|--------|------|-------------|-----|
| POST | `/ai/api/v1/chat-evaluation/datasets` | Upload reusable test case dataset | [v1/chat-evaluation/datasets.md](v1/chat-evaluation/datasets.md) |
| POST | `/ai/api/v1/chat-evaluation/runs` | Start a pipeline evaluation run | [v1/chat-evaluation/run.md](v1/chat-evaluation/run.md) |
| GET | `/ai/api/v1/chat-evaluation/status/{run_id}` | Poll status and retrieve results | [v1/chat-evaluation/status.md](v1/chat-evaluation/status.md) |

Overview: [v1/chat-evaluation/README.md](v1/chat-evaluation/README.md)

## Retrieval Evaluation

Developer/ops tool for measuring retrieval quality. Results are in-memory only (not persisted).

| Method | Path | Description | Doc |
|--------|------|-------------|-----|
| POST | `/ai/api/v1/retrieval-evaluation/run` | Start a batch evaluation run | [v1/retrieval-evaluation/run.md](v1/retrieval-evaluation/run.md) |
| GET | `/ai/api/v1/retrieval-evaluation/{run_id}` | Poll status and retrieve results | [v1/retrieval-evaluation/status.md](v1/retrieval-evaluation/status.md) |

Overview: [v1/retrieval-evaluation/README.md](v1/retrieval-evaluation/README.md)

## Chat (public demo — no JWT in v1)

| Method | Path | Description | Doc |
|--------|------|-------------|-----|
| POST | `/chat/sessions` | Create session for deployed agent | [v1/chat/create-session.md](v1/chat/create-session.md) |
| POST | `/chat/messages` | One agent turn (JSON response) | [v1/chat/send-message.md](v1/chat/send-message.md) |

Overview: [v1/chat/README.md](v1/chat/README.md)

## Voice

| Method | Path | Description |
|--------|------|-------------|
| WS | `/voice/stream` | Voice stream bridge (Twilio / media) |

## Internal (INTERNAL_API_KEY header)

Called by the backend service or workers.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/internal/indexing/ingest` | Trigger KB indexing job |
| DELETE | `/internal/indexing/{kb_entry_id}` | Delete vectors for a KB entry |
| POST | `/internal/evaluations/run` | Trigger evaluation pipeline |
| POST | `/internal/summarisation/run` | Post-ticket summarisation |
| GET | `/internal/health` | Liveness + readiness |

## Product routes (same server, backend JWT)

Not part of `ai/` package but required for chat setup:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/agents/` | Create agent config |
| PUT | `/agents/{id}` | Update draft |
| POST | `/agents/{id}/publish` | Freeze draft as a new version |
| POST | `/agents/{id}/versions/{version_id}/deploy` | Go live with a version for chat |
| GET | `/api-tools/` | List tools to attach to agents |

See [../../backend_docs/api/endpoints.md](../../backend_docs/api/endpoints.md).

## Response formats

| Area | Shape |
|------|--------|
| Chat (`/chat/*`) | Flat Pydantic JSON; errors `{ "detail": "…" }` |
| Product backend | `{ "message", "status_code", "error", "data" }` |

## Code index

| Router | Path |
|--------|------|
| Chat | `ai/src/presentation/api/v1/chat/router.py` |
| Voice | `ai/src/presentation/api/v1/voice/router.py` |
| Indexing | `ai/src/presentation/api/v1/indexing/router.py` |
| Evaluation | `ai/src/presentation/api/v1/evaluation/router.py` |
| Internal | `ai/src/presentation/api/v1/internal/router.py` |
