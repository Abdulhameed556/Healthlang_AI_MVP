# Architecture Overview

The backend follows **Clean / Hexagonal Architecture** with four layers:

| Layer | Package | Responsibility |
|---|---|---|
| Presentation | `backend/src/presentation/` | HTTP routing, Pydantic schemas, `ApiResponse` envelope |
| Application | `backend/src/application/` | Use-cases, commands/results, ports, services |
| Domain | `backend/src/domain/` | Entities, value objects, repository interfaces |
| Infrastructure | `backend/src/infrastructure/` | DB, email providers, S3, Redis, external HTTP |

Dependency rule: **presentation → application → domain ← infrastructure**.

The **AI service** is a separate repo that communicates over internal REST calls.
Both services share the same `JWT_SECRET_KEY` so the AI service can verify tokens
issued by the backend without a round-trip.

## Application module structure

Each bounded context (e.g. `users`, `agents`) uses the same folders:

| Folder | Purpose |
|--------|---------|
| `commands/` | Dataclass input to `execute()` |
| `results/` | Dataclass output from `execute()` |
| `ports/` | Outbound contracts (`Protocol`) |
| `services/` | Stateless helpers (no I/O) |
| `use_cases/` | Orchestration classes |
| `dependencies/providers.py` | FastAPI wiring only |

See `CONTRIBUTING.md` § Application module layout for naming rules and a full
admin invited-user flow diagram.

## API responses

All JSON endpoints return:

```json
{
  "message": "...",
  "status_code": 200,
  "error": false,
  "data": { }
}
```

Implementation: `backend/src/presentation/schemas/api_response.py` and
`backend/src/presentation/error_handlers.py`.

## Email

- Email templates: `backend/src/infrastructure/email/templates/{name}.html` (+ optional `.txt`); send via `TemplateEmailSender` with template name + variables
- Pluggable providers: `log`, `smtp`, `mailgun` via `EMAIL_PROVIDER`
- Use-cases depend on `IInvitationEmailSender` (application port), not Mailgun directly
