# Test Structure Guide — Mirrored, Hexagonal, Layered Testing

This guide documents a battle-tested pytest layout used in a production
Python monorepo (FastAPI + hexagonal architecture). Copy the **rules**, not
just the folder names — the one non-negotiable idea underneath all of it is:

> **`tests/` is a mirror image of `src/`.** If you can't point at the
> production file a test covers just by reading its path, the structure has
> already failed.

Everything else (naming, fixtures, markers, coverage gates) exists to make
that mirror easy to keep honest as the codebase grows to hundreds of files.

---

## Table of contents

1. [Core principle: mirror `src/` exactly](#1-core-principle-mirror-src-exactly)
2. [Top-level layout](#2-top-level-layout)
3. [The three test layers](#3-the-three-test-layers)
4. [Naming conventions](#4-naming-conventions)
5. [conftest.py hierarchy](#5-conftestpy-hierarchy)
6. [Mocking conventions](#6-mocking-conventions)
7. [Testing FastAPI endpoints](#7-testing-fastapi-endpoints)
8. [Testing repositories](#8-testing-repositories)
9. [Factories (factory-boy) for E2E seed data](#9-factories-factory-boy-for-e2e-seed-data)
10. [Markers & skipping slow tests](#10-markers--skipping-slow-tests)
11. [pytest.ini / config](#11-pytestini--config)
12. [Coverage gates & CI](#12-coverage-gates--ci)
13. [Checklist: adding a test for new code](#13-checklist-adding-a-test-for-new-code)
14. [Common mistakes this structure prevents](#14-common-mistakes-this-structure-prevents)
15. [Adapting this to a single-service repo](#15-adapting-this-to-a-single-service-repo)

---

## 1. Core principle: mirror `src/` exactly

If the source layout is hexagonal —

```
src/
├── presentation/   # HTTP: routers, schemas, FastAPI Depends
├── application/    # use-cases / orchestration — no HTTP, no DB
├── domain/         # entities, value objects, exceptions — pure Python
└── infrastructure/ # DB, repositories, email, external HTTP clients
```

— then `tests/unit/` reproduces the **same four folders, in the same
nesting, with the same filenames** (just prefixed `test_`):

| Source file | Test file |
|---|---|
| `application/users/use_cases/create_invited_user_from_admin.py` | `tests/unit/application/users/use_cases/test_create_invited_user_from_admin.py` |
| `application/agents/services.py` | `tests/unit/application/agents/services/test_services.py` |
| `infrastructure/repositories/agents.py` | `tests/unit/infrastructure/repositories/test_agents.py` |
| `infrastructure/email/providers/mail_gun.py` | `tests/unit/infrastructure/email/providers/test_mail_gun.py` |
| `presentation/api/v1/agents/endpoints/create.py` | `tests/unit/presentation/api/v1/agents/endpoints/test_create.py` |

Rules that keep the mirror from rotting:

- **Do not add directory levels that don't exist in `src/`.** If the source
  file is `repositories/agents.py` (a flat file, not a package), the test is
  `tests/unit/infrastructure/repositories/test_agents.py` — **not**
  `tests/unit/infrastructure/repositories/agents/test_agents.py`.
- **One test file per source module.** A source file with 6 functions gets
  one test file with 6 (or more) test functions/classes — not one test file
  per function.
- **Leading underscores are dropped.** A private module `_agent_mappers.py`
  is tested by `test_agent_mappers.py` (no leading underscore on the test
  side — pytest can't collect `test__agent_mappers.py` reliably and it reads
  worse).
- **Name collisions with the stdlib need `__init__.py` chains.** A package
  literally named `email/` (`infrastructure/email/`) will shadow Python's
  stdlib `email` module during collection unless every parent directory from
  `tests/` down has an `__init__.py`. Add them defensively in any package
  whose name might collide with a stdlib or third-party top-level module.

Enforce this at PR review time, not just by convention — a reviewer should
reject any test PR where the test path doesn't have an obvious 1:1 source
counterpart.

---

## 2. Top-level layout

```
tests/
├── __init__.py
├── conftest.py                 # global fixtures + env defaults (all services)
├── test_run_openapi.py         # smoke test: app boots, OpenAPI schema generates
│
└── <service>_tests/            # one root per deployable service, if monorepo
    ├── __init__.py
    ├── conftest.py              # service-wide fixtures (test client, auth headers)
    │
    ├── unit/                    # mirrors src/ — no network, no DB, no filesystem
    │   ├── presentation/
    │   ├── application/
    │   ├── domain/
    │   └── infrastructure/
    │
    ├── integration/              # real DB / cache — mirrors src/infrastructure only
    │   ├── conftest.py            # spins up / tears down real backing services
    │   └── repositories/
    │
    ├── e2e/                       # full HTTP request → response, one folder per API module
    │   ├── auth/
    │   ├── organizations/
    │   └── ...
    │
    └── factories/                 # factory-boy builders for E2E/integration seed data
        ├── user.py
        └── organization.py
```

If your repo is a single service, drop the `<service>_tests/` layer and put
`unit/`, `integration/`, `e2e/`, `factories/` directly under `tests/`.

Real example directory count from the source project (backend service
alone): **~400 test files** mirroring **~400 source files**, organized 1:1.
That ratio is the health metric to watch — if source files start
outnumbering test files by a wide margin, the mirror has stopped being
enforced.

---

## 3. The three test layers

### `unit/` — no I/O, ever

- Every collaborator (DB session, HTTP client, repository, email sender,
  cache) is a mock. Nothing touches a network socket, a filesystem, or a
  real database connection.
- Runs on every commit, every CI run, with no setup required beyond
  `pip install`.
- This is where the bulk of tests live (in the reference project, >80% of
  all test files).

### `integration/` — real backing services, isolated

- Tests infrastructure implementations (repositories, cache adapters,
  vector stores) against a **real** Postgres / Redis / etc.
- Marked with `@pytest.mark.integration` and **excluded from the default
  test run** — they need a running database, so they're opt-in
  (`make test-integration`), not part of the fast feedback loop.
- Until the real fixture (e.g. a transactional `db_session`) exists, the
  whole folder can be stubbed with a module-level skip so collection
  doesn't fail:

  ```python
  """Integration tests require a real database — skipped in default CI/local test runs."""
  import pytest

  pytestmark = pytest.mark.skip(reason="Requires test database — use make test-integration when ready")
  ```

  This is a deliberate, visible placeholder — better than silently missing
  integration tests or letting them fail CI because no DB is configured.

### `e2e/` — full HTTP round-trip

- Drives the app the way a real client would: `AsyncClient` against the
  actual FastAPI `app` object (via `ASGITransport`, no real network socket
  needed), asserting on status code + envelope shape.
- One folder per API module (`e2e/agents/`, `e2e/tickets/`, ...), one test
  file per module (`test_agents_api.py`), grouped in a `Test<Module>API`
  class so related happy-path/edge-case tests read as a suite:

  ```python
  """E2E tests: agents API endpoints."""


  class TestAgentsAPI:
      async def test_happy_path(self, async_client, auth_headers):
          ...
  ```

- Seeds data via `factories/`, not hand-rolled dict literals — see §9.

---

## 4. Naming conventions

| Thing | Convention | Example |
|---|---|---|
| Test file | `test_<source_filename>.py` | `create_agent.py` → `test_create_agent.py` |
| Test function | `test_<method>_<condition>_<expected_outcome>` | `test_execute_raises_when_active_user_exists` |
| Fixture-producing test class (E2E) | `Test<Module>API` | `TestAgentsAPI` |
| Marker for slow/external tests | `integration` | `@pytest.mark.integration` |
| Private source module test | drop the leading underscore | `_agent_mappers.py` → `test_agent_mappers.py` |

Test function names should be readable as a sentence describing behavior,
not implementation: `test_execute_reinvites_existing_non_active_user`, not
`test_case_3` or `test_execute_2`.

---

## 5. `conftest.py` hierarchy

Fixtures live at the narrowest scope that needs them — don't put a
single-test fixture in the root conftest just because it's convenient.

```
tests/conftest.py                       # env vars + process-wide singletons
tests/<service>_tests/conftest.py       # service test client + auth fixtures
tests/<service>_tests/integration/conftest.py   # real DB/cache setup+teardown
tests/<service>_tests/unit/core/conftest.py     # narrow fixtures for one subtree
```

**Root `tests/conftest.py`** — set environment variables *before* any
module-level `Settings()` singleton gets instantiated during collection, and
register any process-wide fakes (e.g. a stub message-broker so
`@task`-decorated functions can register without a real queue connection):

```python
"""Root conftest — sets env defaults before any Settings() singleton
is instantiated during collection."""
import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://localhost/app_test")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret")
```

Use `setdefault`, not a hard assignment, so a real `.env` (loaded by some
library before conftest runs) doesn't silently override your test config —
unless you specifically need to force a value regardless of `.env`, in which
case assign directly and **comment why**.

**Service-level conftest** — the reusable `async_client` fixture that every
endpoint test needs, with dependency overrides pre-cleared:

```python
@pytest.fixture()
async def async_client(monkeypatch):
    from unittest.mock import AsyncMock

    # Neutralize real startup/shutdown side effects (DB pings, external calls).
    monkeypatch.setattr("service.src.main.verify_required_dependencies", AsyncMock())
    monkeypatch.setattr("service.src.main.close_database_connection", AsyncMock())

    from service.src.main import app
    from httpx import ASGITransport, AsyncClient

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
```

**Integration conftest** — owns the lifecycle of the real backing service
(spin up test DB / transaction, tear down after each test). Keep this
isolated so unit tests never accidentally import it.

---

## 6. Mocking conventions

Consistency here is what makes tests reviewable at a glance:

- **`AsyncMock`** for anything `await`ed: repository methods, use-case
  `execute()`, external HTTP calls, email senders.
- **`MagicMock`** for sync methods on otherwise-async objects — e.g.
  `session.add(...)` on an `AsyncSession` is synchronous even though the
  session is async. Assert with `.assert_called_once()`, **not**
  `.assert_awaited_once()` — using the wrong assertion silently passes on a
  `MagicMock` even if the code path is wrong.
- **Assert on call args, not just call count**, when the mutation matters:

  ```python
  org_arg: Organization = use_case._organization_repository.add.await_args.args[0]
  assert org_arg.status == OrganizationStatus.INVITED
  ```

- **Fixture factories over inline mocks** when a use-case has 4+
  collaborators — build the wired-up object once in a `@pytest.fixture()`,
  and override just the return values each test needs:

  ```python
  @pytest.fixture()
  def use_case() -> CreateInvitedUserFromAdmin:
      org_repo = AsyncMock()
      user_repo = AsyncMock()
      user_repo.get_by_email = AsyncMock(return_value=None)
      ...
      return CreateInvitedUserFromAdmin(
          organization_repository=org_repo,
          user_repository=user_repo,
          ...
      )
  ```

- **Assert call order when ordering is a real invariant** (e.g. "commit the
  transaction before sending the email, not after"):

  ```python
  call_order: list[str] = []
  use_case._unit_of_work.commit = AsyncMock(side_effect=lambda: call_order.append("commit"))
  use_case._email_sender.send = AsyncMock(side_effect=lambda **_: call_order.append("email"))
  ...
  assert call_order == ["commit", "email"]
  ```

---

## 7. Testing FastAPI endpoints

Unit-test endpoints by overriding `Depends`, hitting the app through the
shared `async_client` fixture, and asserting on the response envelope — not
by testing the router function directly.

```python
@pytest.mark.asyncio
async def test_create_agent_returns_201(async_client) -> None:
    auth = _auth_context()
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=_create_result())

    app.dependency_overrides[require_org_inviter] = lambda: auth
    app.dependency_overrides[get_create_agent] = lambda: mock_use_case
    try:
        response = await async_client.post("/api/v1/agents", json={...})
        assert response.status_code == 201
    finally:
        app.dependency_overrides.clear()
```

Rules:

- **Always clear overrides in `finally`.** Leaked `dependency_overrides`
  bleed into unrelated tests and cause flaky, order-dependent failures.
- **Match the real dependency, not a stand-in.** If the handler depends on
  `require_org_inviter` for mutations and `require_auth` for reads, override
  exactly that — don't blanket-override auth for every test.
- **Test authorization boundaries explicitly.** e.g. a "read-only role gets
  403" test should override *only* the auth dependency with a read-only
  user and leave the real permission-check dependency unmocked, so the
  actual authorization logic runs and is what's being verified — not a
  mocked stand-in for it.

---

## 8. Testing repositories

Repositories wrap an ORM session — mock the session, not the database:

```python
@pytest.mark.asyncio
async def test_exists_by_name_in_organization_returns_true() -> None:
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = uuid4()
    session.execute = AsyncMock(return_value=result)

    repository = SqlAlchemyAgentRepository(session)
    assert await repository.exists_by_name_in_organization(uuid4(), "Support Bot") is True
    session.execute.assert_awaited_once()
```

- `session.execute(...)` is async → `AsyncMock`.
- The `Result` object returned by `execute()` has sync accessor methods
  (`.scalar_one_or_none()`, `.scalars()`) → `MagicMock`.
- This is a *unit* test of the repository's query-building and
  row→entity mapping logic — it proves "given this DB response shape, the
  repository returns/raises the right thing," not "this SQL is valid
  against a real schema." That correctness belongs to `integration/`.

---

## 9. Factories (factory-boy) for E2E seed data

E2E and integration tests should build fixtures through **factories**, not
inline dict/object literals repeated across test files — the payoff is that
when an entity gains a required field, you update one factory instead of
every test file that constructs one.

```python
# tests/factories/organization.py
import factory

from src.domain.organizations.entities import Organization
from src.domain.organizations.value_objects import OrganizationStatus


class OrganizationFactory(factory.Factory):
    class Meta:
        model = Organization

    name = factory.Faker("company")
    industry = "fintech"
    status = OrganizationStatus.ACTIVE
```

```python
# usage in an e2e test
org = OrganizationFactory(name="Acme Corp")
```

One factory file per entity, named after the entity (`organization.py`,
`user.py`), living flat under `tests/factories/` (or
`tests/<service>_tests/factories/` in a monorepo) — not nested by layer,
since factories aren't part of the hexagonal mirror; they're test
infrastructure that spans layers.

---

## 10. Markers & skipping slow tests

Declare custom markers in `pytest.ini` so `pytest --strict-markers` doesn't
reject them, and so `pytest -m integration` / `pytest -m "not integration"`
work:

```ini
[pytest]
markers =
    integration: tests that require a real database (run separately)
```

Use the marker at module level when an entire file needs it:

```python
pytestmark = pytest.mark.integration
```

Default CI/local runs should **exclude** `integration` (fast feedback);
a separate CI job or `make` target runs the marked tests against a real
service.

---

## 11. pytest.ini / config

```ini
[pytest]
pythonpath = .
testpaths = tests
asyncio_mode = auto
markers =
    integration: tests that require a real database (run separately)
addopts =
    --import-mode=importlib
    -v
    --cov=src
    --cov-report=term-missing
    --cov-fail-under=90
```

Notes:

- `asyncio_mode = auto` — every `async def test_...` runs without needing
  `@pytest.mark.asyncio` on each one (still fine to add it explicitly for
  clarity/consistency, as shown in the examples above; it's harmless either
  way under `auto` mode).
- `--import-mode=importlib` avoids `sys.path` collisions between
  same-named test modules in different packages (`admin_tests/unit/core/test_config.py`
  vs `backend_tests/unit/core/test_config.py`) — required in any repo with
  more than one `test_config.py` anywhere in the tree.
- `--cov-fail-under=90` makes coverage a **hard CI gate**, not a
  dashboard number nobody looks at.

---

## 12. Coverage gates & CI

Wire test layers to `make` targets so both humans and CI run the same
commands:

```makefile
test:
	pytest tests/ --cov=src --cov-fail-under=90

test-integration:
	pytest tests/ -m integration

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/
```

CI (`.github/workflows/ci.yml`) should run `make lint` then `make test` on
every push/PR into the main integration branch — fail the build on lint
errors or on dropping below the coverage floor, not just on test failures.

---

## 13. Checklist: adding a test for new code

When you add any new source file, before opening the PR:

- [ ] Test file exists at the **mirrored path** under `tests/unit/`.
- [ ] Every public function/method has at least: one happy-path test, one
      test per distinct error/exception branch.
- [ ] All I/O (DB, HTTP, cache, filesystem, email) is mocked in the unit
      test — if it isn't, the test belongs in `integration/`, not `unit/`.
- [ ] If it's a new use-case: unit test asserts on **both** the returned
      result *and* the side effects (what got saved, what got called, and
      in what order if order matters).
- [ ] If it's a new endpoint: an e2e test exists exercising the real
      request → response cycle, plus a unit test with `dependency_overrides`
      for each distinct auth/role branch.
- [ ] If it's a new repository method: unit test with a mocked session,
      plus (if a real test DB is available) an integration test.
- [ ] `dependency_overrides` cleared in `finally` for every endpoint test.
- [ ] Coverage did not drop below the configured floor.

---

## 14. Common mistakes this structure prevents

| Mistake | Why the structure prevents it |
|---|---|
| "Where's the test for this file?" scavenger hunts | 1:1 mirrored path — the answer is always `tests/<layer>/<same path>` |
| Tests that pass locally, fail in CI (or vice versa) | `integration` tests are explicitly marked and separated from the default fast run |
| Flaky tests from leaked FastAPI dependency overrides | Convention: always `app.dependency_overrides.clear()` in `finally` |
| Silent regressions in untested error branches | Checklist requires one test per exception branch, not just the happy path |
| Divergent seed data across dozens of e2e tests | Centralized `factories/`, one per entity |
| A repo where "coverage" is a vanity badge nobody enforces | `--cov-fail-under` as a hard `pytest` exit-code gate wired into CI |

---

## 15. Adapting this to a single-service repo

Everything above assumes a monorepo with multiple deployable services
(`backend_tests/`, `admin_tests/`, `ai_tests/`, each with their own
`unit/integration/e2e`). For a single-service repo, collapse one level:

```
tests/
├── conftest.py
├── unit/
│   ├── presentation/
│   ├── application/
│   ├── domain/
│   └── infrastructure/
├── integration/
├── e2e/
└── factories/
```

The mirroring rule (§1), naming conventions (§4), mocking conventions (§6),
and coverage gate (§12) all apply unchanged — the only thing that goes away
is the extra `<service>_tests/` nesting level and the need for per-service
`conftest.py` env var isolation.
