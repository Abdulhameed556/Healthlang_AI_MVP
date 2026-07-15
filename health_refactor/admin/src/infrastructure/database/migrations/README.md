# Admin migrations (retired)

**All schema migrations for the shared Postgres database are owned by the backend Alembic project.**

- Config: `backend/src/infrastructure/database/migrations/alembic.ini`
- Revisions: `backend/src/infrastructure/database/migrations/versions/`
- Version table: `alembic_version_backend` (not `alembic_version`)

Apply everything (product backend, admin panel tables, `admin_otps`, etc.) with:

```bash
make migrate
```

Do **not** add new files under this directory. Change admin ORM models in
`admin/src/infrastructure/database/models/`, then generate a revision from the
repo root:

```bash
make migrate-gen name="describe_change"
```

Admin tables are excluded from autogenerate in `backend/.../migrations/env.py`
(`IGNORED_TABLES`); add admin schema changes as **hand-written** revisions in
the backend `versions/` folder (same as `admin_otps` and admin panel core tables).
