# Admin Panel API — Documentation

Frontend integration docs for the Admin Panel API (`/api/v1`).

## Structure

```
docs/api/
├── README.md           ← you are here
├── endpoints.md        ← quick reference table (all routes)
└── v1/
    ├── auth/           ← matches src/presentation/api/v1/auth/
    ├── users/
    ├── organizations/
    └── dashboard/
```

Each implemented endpoint gets a file under `v1/<module>/` with sample
request/response payloads, auth requirements, and frontend notes.

**No endpoint docs are written until that route is implemented.**

See `../../.cursor/rules/api-documentation.mdc` for the required template and
when to document.
