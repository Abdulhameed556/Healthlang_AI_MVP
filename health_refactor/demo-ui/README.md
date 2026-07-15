# Demo UI

Minimal browser UI to demonstrate the full agent workflow before building the production frontend.

## What it does

1. **Login** — email/password against the backend (`POST /api/v1/auth/login`)
2. **Agents** — list, create, edit, view, publish, and deploy agent versions via backend API
3. **API tools** — list, create, edit, view, delete, and test tools (`/api/v1/api-tools`)
4. **Test chat** — create a session and send messages via the same API (AI routes mounted on backend)

## Prerequisites

See **[docs/setup.md](../docs/setup.md)** for install (Python, Postgres, Redis, `.env`, migrations, LLM keys).

- Product API running on **port 8000** (backend + AI in one process)
- `APP_ENV=development` in `.env` (demo UI is **not** served in production)
- Postgres, Redis, and env vars configured as usual

## Run

From the **repo root**:

```bash
make dev-backend  # product + AI + demo UI on :8000
make dev-demo     # open http://localhost:8000/demo/
```

Direct URL:

```
http://localhost:8000/demo/
```

`config.js` uses the same origin for backend and chat — no second port.

## API endpoints used

| Step | Endpoint |
|------|----------|
| Login | `POST /api/v1/auth/login` |
| List agents | `GET /api/v1/agents/` |
| Create agent | `POST /api/v1/agents/` |
| Publish version | `POST /api/v1/agents/{id}/publish` |
| Deploy version | `POST /api/v1/agents/{id}/versions/{version_id}/deploy` |
| List versions | `GET /api/v1/agents/{id}/versions` |
| List API tools | `GET /api/v1/api-tools/` |
| Create API tool | `POST /api/v1/api-tools/` |
| Update API tool | `PUT /api/v1/api-tools/{id}` |
| Test draft tool | `POST /api/v1/api-tools/test` |
| Test saved tool | `POST /api/v1/api-tools/{id}/test` |
| New session | `POST /api/v1/chat/sessions` |
| Send message | `POST /api/v1/chat/messages` |

## Config

Defaults are derived from `window.location.origin`. Override in `config.js` only if you run the UI from a different host than the API.

## Notes

- Agents must have a **deployed version** before starting a test chat session (Publish a draft, then Deploy that version — or use **Publish & deploy** in the chat sidebar).
- Agent timezone options come from `agent-catalog.js` (keep in sync with `backend/src/domain/agents/timezones.py`).
- Sessions are created with `metadata.mode = "test"`.
- Auth is only on backend routes; chat endpoints are open for this internal demo.
- `make dev-ai` remains available for a standalone AI process (e.g. future WebSocket split) but is not required for the demo.
