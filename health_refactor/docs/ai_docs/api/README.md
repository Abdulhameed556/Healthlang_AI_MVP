# AI Service API — Documentation

Integration docs for AI routes mounted at `/api/v1` on the **shared product server**
(same port as backend — typically `:8000`).

Used by the demo UI, future product frontend, and internal backend callbacks.

## Structure

```
docs/ai_docs/api/
├── README.md           ← you are here
├── endpoints.md        ← quick reference (all routes)
└── v1/
    ├── chat/           ← sessions + messages (implemented)
    ├── voice/          ← WebSocket (planned / partial)
    ├── evaluation/
    ├── indexing/
    └── internal/       ← backend → AI (API key auth)
```

## Chat (documented)

| Doc | Method | Path |
|-----|--------|------|
| [v1/chat/README.md](v1/chat/README.md) | — | Overview + field reference |
| [v1/chat/create-session.md](v1/chat/create-session.md) | POST | `/api/v1/chat/sessions` |
| [v1/chat/send-message.md](v1/chat/send-message.md) | POST | `/api/v1/chat/messages` |

Chat responses use **flat JSON**, not the product API `{ message, data, error }` envelope.

## Architecture

How chat connects to deployed agents and the LangGraph pipeline:

- [../architecture/overview.md](../architecture/overview.md)
- [../architecture/chat-pipeline.md](../architecture/chat-pipeline.md)
- [../pipelines/chat_runtime.md](../pipelines/chat_runtime.md)

## Local development

```bash
make dev-backend   # product + AI + demo UI on :8000
```

Demo UI: `http://localhost:8000/demo/`  
OpenAPI (when `APP_DEBUG=true`): `http://localhost:8000/docs`

## Related product docs

Agent configuration and deploy (required before chat):

- [../../backend_docs/api/v1/agents/README.md](../../backend_docs/api/v1/agents/README.md)

API tools attached to agents:

- [../../backend_docs/api/v1/api_tools/README.md](../../backend_docs/api/v1/api_tools/README.md)
