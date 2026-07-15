# Product Dashboard — Backend Service

Multi-tenant SaaS backend built with **FastAPI + PostgreSQL**, with an integrated **AI
chat pipeline** and internal **demo UI** for agent configuration and test chat.

## Quick start

See **[docs/setup.md](docs/setup.md)** for full install steps (Python, Postgres, Redis,
`.env`, migrations, LLM keys).

```bash
cp .env.example .env          # edit DATABASE_URL, JWT, LLM keys, etc.
pip install -r requirements.txt
make migrate
make dev-backend              # product + AI + demo UI → http://localhost:8000
make dev-demo                 # open http://localhost:8000/demo/
```

## Test & lint

From the repo root, with Python 3.11 and dependencies installed:

```bash
pip install -r requirements.txt   # once
make lint                         # ruff check
make test                         # unit + integration, 90% coverage gate
make format                       # optional: ruff format
make test-integration             # integration only (needs test DB)
```

Ensure `.env` is populated from `.env.example` before running tests. CI uses
`DATABASE_URL` and `JWT_SECRET_KEY` from GitHub Actions env; locally those are
read from `.env` or defaults in `tests/conftest.py`.

See [CONTRIBUTING.md](CONTRIBUTING.md#test-and-lint) for details.

See [docs/backend_docs/git-workflow.md](docs/backend_docs/git-workflow.md) for branching
and release process.

## Documentation

| Area | Path |
|------|------|
| **Local setup** | [docs/setup.md](docs/setup.md) |
| Backend API | [docs/backend_docs/api/README.md](docs/backend_docs/api/README.md) |
| AI architecture | [docs/ai_docs/architecture/overview.md](docs/ai_docs/architecture/overview.md) |
| Chat API | [docs/ai_docs/api/v1/chat/README.md](docs/ai_docs/api/v1/chat/README.md) |
| Demo UI | [demo-ui/README.md](demo-ui/README.md) |

## Demo UI (agent setup + test chat)

Internal workflow demo — login, create/deploy agents, configure API tools, test chat.
Static files live in `demo-ui/` and are **served by the product API** at `/demo/` when
`APP_ENV=development`.

```bash
make dev-backend
make dev-demo
```

See [demo-ui/README.md](demo-ui/README.md) for details.
