# SupportOS — Work Handoff

This file is the single source of truth for what has been built and what is pending.
When starting a new conversation, share this file and say "continue from HANDOFF.md".

---

## Repo Structure

```
SupportOs-backend/
├── backend/          # FastAPI backend (orgs, agents, KB, auth, tickets, tags)
├── ai/               # AI service (indexing, retrieval, evaluation, chat pipeline)
├── admin/            # Admin service
├── demo-ui/          # Internal-only demo UI (served at /demo in development)
├── tests/            # All unit tests (backend + ai + admin)
└── HANDOFF.md        # This file
```

Services all run on one FastAPI app mounted at:
- `backend` → `/api/v1/`
- `ai`      → `/ai/api/v1/`
- `admin`   → `/admin/api/v1/`

**Start command:** `uvicorn run:root_app --reload` (NOT `uvicorn backend.src.main:app` — that only loads the backend service and won't show AdminAuth in Swagger)

**Swagger URL:** `http://127.0.0.1:8000/docs`

**Worker command:** `$env:PYTHONPATH="."; dramatiq ai.src.infrastructure.workers.worker --processes 1 --threads 8`
Or: `make worker` (on Linux/Mac)

---

## Active Branch

`feature/KB-endpoints-and-actions-optimization` — PR #23, open against `dev`.

---

## What Has Been Built

### 1. KB Indexing Pipeline (ai service) ✅

**Purpose:** When a document is uploaded to S3 and confirmed, a Dramatiq background worker
parses → chunks → embeds → upserts into Pinecone.

**Key files:**
- `ai/src/application/indexing/pipeline.py` — pipeline orchestrator
- `ai/src/application/indexing/dependencies.py` — wires concrete deps
- `ai/src/infrastructure/workers/tasks/indexing.py` — Dramatiq actor (`ingest_document`, `delete_document`)

**Critical fix already applied:**
The Dramatiq worker calls `asyncio.run()` per task, which creates a new event loop each time.
The SQLAlchemy `engine` singleton kept asyncpg connections bound to the old loop.
Fix: `await engine.dispose()` at the top of every async task before running the pipeline.
This is already in `indexing.py` — **do not remove it**.

**Critical broker fix applied (this session):**
`ai/src/infrastructure/workers/broker.py` was missing the import of the `indexing` task module.
`ingest_document` and `delete_document` actors were never registered, causing
`ActorNotFound` errors in the worker. Fixed by adding:
```python
from ai.src.infrastructure.workers.tasks import indexing as _indexing  # noqa: F401, E402
```

**Pinecone scoping:** Vectors are upserted per `agent_id`. If no agents are linked to the KB
at indexing time, `UpsertVectorsStep` silently skips (`if not ctx.agent_ids: return`).
To get vectors into Pinecone: create an agent, link it to the KB, THEN index the entry.

**Supported file types:** `docx`, `txt`, `md` — all uploaded via S3 presigned URL.
There is NO inline text entry endpoint — users must upload a `.txt` file the same way as `.docx`.

---

### 2. KB Retrieval Evaluation Pipeline (ai service) ✅

**Purpose:** Internal developer tool to score how well a KB document retrieves relevant chunks.
Runs via the demo-ui or directly via API.

**Evaluation type:** Retrieval-only. Three DeepEval metrics:
- `contextual_relevancy` — are retrieved chunks on-topic?
- `contextual_precision` — are the best chunks ranked first?
- `contextual_recall` — is all needed info covered?

**Pipeline steps:**
1. `LoadSourceChunksStep` — loads entry from DB, downloads from S3, parses, chunks
2. `SynthesizeTestsetStep` — uses DeepEval synthesizer to generate (question, expected_answer) goldens
3. `RunTestCasesStep` — for each golden: retrieve from Pinecone → score with 3 metrics

**Key files:**
- `ai/src/application/retrieval_evaluation/pipeline.py`
- `ai/src/infrastructure/retrieval_evaluation/scorer.py`
- `ai/src/infrastructure/retrieval_evaluation/run_store.py` — in-memory, keyed by `run_id`

**API endpoints:**
- `POST /ai/api/v1/retrieval-evaluation/run` — start a run, returns `run_id`
- `GET  /ai/api/v1/retrieval-evaluation/{run_id}` — poll status / get results

**Common 0% score cause:** Retrieved chunks = 0. This means the agent has no vectors in
Pinecone for that KB. Re-index the entry with the agent already linked first.

---

### 3. KB Backend — Full Implementation ✅

All endpoints are implemented, tested, and documented. PR #23 is open against `dev`.

#### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET`  | `/knowledge-base/` | List all KBs for org (paginated, with entry count + attached agents) |
| `POST` | `/knowledge-base/` | Create KB container |
| `PATCH`| `/knowledge-base/{kb_id}` | Update KB name / description |
| `DELETE`| `/knowledge-base/{kb_id}` | Delete KB and all entries |
| `POST` | `/knowledge-base/{kb_id}/entries/upload-url` | Get presigned S3 URL (step 1 of upload) |
| `POST` | `/knowledge-base/{kb_id}/entries/{entry_id}/confirm-upload` | Confirm upload, queue indexing |
| `GET`  | `/knowledge-base/{kb_id}/entries` | List entries (returns `kb_name`, `kb_description` on each item) |
| `PATCH`| `/knowledge-base/{kb_id}/entries/{entry_id}` | Entry lifecycle action (see below) |
| `DELETE`| `/knowledge-base/{kb_id}/entries/{entry_id}` | Hard delete + Pinecone vector cleanup |
| `POST` | `/knowledge-base/{kb_id}/agents/{agent_id}` | Attach agent to KB |
| `DELETE`| `/knowledge-base/{kb_id}/agents/{agent_id}` | Detach agent from KB |

#### PATCH entry — actions only

`action` is **required**. No name/description fields. Three values:
```json
{ "action": "archive" }    // soft-delete (is_archived=true)
{ "action": "unarchive" }  // restore (is_archived=false), re-queues indexing
{ "action": "retry" }      // re-queues indexing for failed entries
```

#### GET /knowledge-base/ response shape (new this session)

```json
{
  "items": [{ "kb_id": "...", "name": "...", "description": "...", "entry_count": 5, "attached_agents": [...], "created_at": "...", "updated_at": "..." }],
  "total": 1, "page": 1, "page_size": 20, "total_pages": 1
}
```
`entry_count` = non-archived entries only.

#### GET /entries response — new fields this session

Each entry item now includes:
- `kb_name` — display name of the parent KB
- `kb_description` — description of the parent KB (null if not set)

#### What was removed this session

- `create_text_entry` endpoint and use case — deleted entirely. Upload `.txt` files via S3.
- `UpdateEntry` use case — deleted entirely. PATCH endpoint does actions only.
- `update_entry.md` doc — deleted (no longer relevant).
- `create-text-entry.md` doc — deleted.

#### DB Model: `knowledge_base_entries`

Columns (all exist in migrations):
- `id`, `knowledge_base_id`, `created_by`, `name`, `description`
- `file_type` — `docx`, `txt`, `md`
- `storage_path` — S3 key
- `content_text` — exists in DB but nothing writes to it. Do not drop — would cause migration conflicts.
- `indexing_status` — `processing`, `indexed`, `failed`
- `is_archived` — bool
- `file_size_bytes` — BigInteger, nullable
- `created_at`, `updated_at`

#### Delete flow

Hard delete → calls `delete_document` Dramatiq actor → removes all Pinecone vectors for that entry.
Archive → soft-delete only, vectors stay in Pinecone.

---

### 4. Demo UI (internal tool) ✅

**Location:** `demo-ui/` — served at `http://localhost:8000/demo`

**Workflow:**

| Step | View | Purpose |
|------|------|---------|
| 1 | Sign in | Auth with backend credentials |
| 2 | Agents | Create/edit/deploy agents; manage API tools |
| 3 | Test chat | Live multi-turn chat against a deployed agent |
| 4 | Retrieval eval | Score KB document retrieval using DeepEval |
| 5 | Tags | Manage org classification tags (added by partner in PR #22) |

**Files:**
- `demo-ui/config.js` — base URLs
- `demo-ui/eval-ui.js` — retrieval eval UI (our addition)
- `demo-ui/tags-ui.js` — tags UI (partner's addition, PR #22)

---

### 5. Tag System (backend) — Merged via PR #22 ✅

Built by Samuelafriex. Full org-scoped tag CRUD + AI ticketing agent integration.

**What it does:**
- Admins create classification tags (e.g. `refund_request`) scoped to their org
- After a chat closes, the AI ticketing agent auto-tags the generated ticket using the org's tag catalog
- Ticket list endpoint supports tag-based filtering

**Endpoints:** `GET/POST/PATCH/DELETE /api/v1/tags/`

**AI integration:** `post_close_pipeline.py` loads org tags and passes them as `allowed_tags`
to the ticketing agent. Gracefully degrades — if tag loading fails, ticket is created without tags.

**Files:**
- `backend/src/domain/tags/` — entities, repos, exceptions, value objects
- `backend/src/application/tags/` — use cases (CRUD)
- `backend/src/infrastructure/repositories/tags.py` — SQLAlchemy impl
- `backend/src/presentation/api/v1/tags/` — endpoints + schemas
- `docs/backend_docs/api/v1/tags/` — full docs

---

## What Is Pending

### A. Chat Evaluation ⬅ NEXT TASK

The partner built the chat pipeline. We need to build evaluation for it — scoring how well
the AI responds across a set of test conversations.

**Context:**
- Chat pipeline lives in `ai/src/application/chat/`
- The retrieval evaluation (done) used DeepEval metrics: `contextual_relevancy`, `contextual_precision`, `contextual_recall`
- Chat eval will need different metrics (e.g. answer relevancy, faithfulness, hallucination)
- The approach should mirror the retrieval eval pattern: pipeline → run store → polling endpoint
- Branch from `dev` for this work

**Start point for next chat:** Read `ai/src/application/chat/` to understand the chat pipeline,
then plan the evaluation module from scratch.

---

### B. AWS S3 Credentials

Before testing any S3-dependent endpoints, add to `.env`:
```env
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<secret>
AWS_REGION=<region>
S3_BUCKET_NAME=<bucket>
```

### C. Alembic — run before deploying

```bash
alembic upgrade head
```

All migrations are committed and in sync.

---

## Key Environment Variables

```env
# OpenAI
OPENAI_API_KEY=<key>
DEFAULT_JUDGE_MODEL=gpt-4o-mini
DEFAULT_CHAT_MODEL=gpt-4o-mini

# Pinecone
PINECONE_API_KEY=<key>
PINECONE_INDEX_NAME=<index>

# DB
DATABASE_URL=postgresql+asyncpg://...

# Redis (Dramatiq broker)
DRAMATIQ_BROKER_URL=redis://localhost:6379

# Internal auth (AI service)
INTERNAL_API_KEY=<key>

# AWS (required for all KB uploads)
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<secret>
AWS_REGION=<region>
S3_BUCKET_NAME=<bucket>
```

---

## Commit Style

- Past-tense subject verbs: `added`, `fixed`, `removed`, `implemented`, `updated`
- No `Co-Authored-By` lines
- No Claude attribution in commits

---

## Important Gotchas

1. **Never remove `await engine.dispose()`** from the Dramatiq task in `indexing.py`.
   It prevents asyncpg "event loop is closed" crashes on every worker invocation.

2. **`broker.py` must import all task modules** — actors are only registered when their
   module is imported. If a new task file is added, add an import to `broker.py` or
   the worker will throw `ActorNotFound` and move messages to the DLQ.

3. **Pinecone vectors are scoped by `agent_id`**. Evaluation returns 0% with "Retrieved Chunks (0)"
   when the agent has no vectors — re-index the entry with the agent linked first.

4. **Windows + uvloop**: uvloop is Linux-only. The Windows guard in `run.py` must stay.

5. **`content_text` column**: Exists in DB model and initial migration. No use case writes to it.
   Do not create a migration to drop it.

6. **Run `uvicorn run:root_app --reload`** not `uvicorn backend.src.main:app`.
   The combined app has both `AdminAuth` and `BackendAuth` in Swagger.
   The backend-only app only has `BackendAuth`.

7. **ruff line-length = 100** — IDE E501 warnings at 79 chars are false positives. Ignore them.
