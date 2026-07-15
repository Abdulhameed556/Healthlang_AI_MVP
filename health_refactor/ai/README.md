# Product Dashboard — AI Service

Inference and pipeline backend for the Product Dashboard platform.

Handles:
- **Single-task agent** — one-shot LLM calls (`run`, `stream`, structured tag → JSON)
- **Chat runtime** — streaming SSE agent conversations
- **Voice runtime** — WebSocket agent conversations (Twilio Media Streams)
- **Evaluation** — simulated user + AI judge pipeline
- **Indexing** — knowledge-base document ingestion → vector store
- **Retrieval** — semantic search for RAG
- **Tool executor** — agent → external API calls
- **Summarisation** — post-interaction TICKET_SUMMARY generation

## Quick start

Use the **repo root** Makefile (monorepo `.env` at project root):

```bash
cp .env.example .env          # from repo root — set DATABASE_URL at minimum
docker compose up -d
make dev-backend              # product + AI API + demo UI on :8000
make dev-demo                 # open http://localhost:8000/demo/
```

Optional: `make dev-ai` runs AI alone on :8001 (e.g. future WebSocket split).

Run background workers in a second terminal when testing indexing jobs:

```bash
make worker                   # from ai/ directory, or see ai/Makefile
```

## Test & lint

From the repo root, with Python 3.11 and dependencies installed:

```bash
pip install -r requirements.txt   # once
make lint                         # ruff check src/ tests/
make test                         # unit + integration, 90% coverage gate
make format                       # optional: ruff format src/ tests/
make test-integration             # integration only (needs vector store / Redis)
```

Ensure `.env` is populated from `.env.example` before running tests. CI uses
`JWT_SECRET_KEY`, `INTERNAL_API_KEY`, and `VECTOR_STORE_URL` from GitHub Actions
env; locally those are read from `.env` or defaults in `tests/conftest.py`.

See [CONTRIBUTING.md](CONTRIBUTING.md#test-and-lint) for details.

See [docs/git-workflow.md](docs/git-workflow.md) for branching and release process.
See [docs/](../docs/ai_docs/) for architecture and pipeline docs.

**Single-task agent** (providers, structured XML output): [docs/ai_docs/single_task_agent.md](../docs/ai_docs/single_task_agent.md)
