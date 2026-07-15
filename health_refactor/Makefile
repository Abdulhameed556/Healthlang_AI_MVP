.PHONY: help \
        dev dev-backend dev-admin dev-ai dev-stack dev-demo \
        worker \
        test test-backend test-admin test-ai \
        lint format \
        migrate migrate-gen migrate-down \
        admin-migrate admin-migrate-gen admin-migrate-down \
        seed


ALEMBIC_BACKEND = PYTHONPATH=. alembic -c backend/src/infrastructure/database/migrations/alembic.ini

BACKEND_APP = backend.src.main:app
AI_APP      = ai.src.main:app
BACKEND_PORT = 8000
AI_PORT      = 8001
DEMO_URL     = http://localhost:$(BACKEND_PORT)/demo/

# ── Help ───────────────────────────────────────────────────────────────


help:
	@echo "Dev servers"
	@echo "  make dev-backend   Product + AI API + demo UI → http://localhost:$(BACKEND_PORT)"
	@echo "  make dev-demo      Print demo URL and open browser"
	@echo "  make dev-admin     Admin API    → http://localhost:8002"
	@echo "  make dev           Monorepo app (admin + backend + AI, port $(BACKEND_PORT))"
	@echo "  make dev-ai        Optional: AI-only on :$(AI_PORT) (future WebSocket split)"
	@echo "  make worker        Dramatiq background worker (requires Redis)"
	@echo ""
	@echo "Demo workflow"
	@echo "  1. make dev-backend"
	@echo "  2. make dev-demo        # open $(DEMO_URL)"
	@echo ""
	@echo "Tests: make test | test-backend | test-ai | test-admin"
	@echo "DB:    make migrate | migrate-gen name=\"...\""

# ── Dev ────────────────────────────────────────────────────────────────
dev:
	uvicorn run:root_app --reload --port $(BACKEND_PORT)

dev-backend:
	@test -f .env || (echo "Missing .env — run: cp .env.example .env" && exit 1)
	PYTHONPATH=. uvicorn $(BACKEND_APP) --reload --host 0.0.0.0 --port $(BACKEND_PORT)

dev-admin:
	PYTHONPATH=. uvicorn admin.src.main:app --reload --host 0.0.0.0 --port 8002

dev-ai:
	@test -f .env || (echo "Missing .env — run: cp .env.example .env" && exit 1)
	@echo "Optional standalone AI service (use dev-backend for normal local dev)."
	PYTHONPATH=. uvicorn $(AI_APP) --reload --host 0.0.0.0 --port $(AI_PORT)

# Alias — one server is enough for demo + chat HTTP.
dev-stack: dev-backend

# ── Background workers ─────────────────────────────────────────────────
# Runs the Dramatiq worker that processes queued jobs (requires Redis).
worker:
	@test -f .env || (echo "Missing .env — run: cp .env.example .env" && exit 1)
	PYTHONPATH=. dramatiq ai.src.infrastructure.workers.worker --processes 1 --threads 8

# Demo static files are served by backend at /demo when demo-ui/ exists.
dev-demo:
	@echo "Demo UI: $(DEMO_URL)"
	@echo ""
	@echo "Requires: make dev-backend"
	@command -v open >/dev/null 2>&1 && open "$(DEMO_URL)" || true

# ── Tests ──────────────────────────────────────────────────────────────
test:
	pytest tests/ --cov=backend/src --cov=admin/src --cov=ai/src --cov-fail-under=90

test-backend:
	pytest tests/backend_tests/ --cov=backend/src --cov-fail-under=90

test-admin:
	pytest tests/admin_tests/ --cov=admin/src --cov-fail-under=90

test-ai:
	pytest tests/ai_tests/ --cov=ai/src --cov-config=.coveragerc-ai

# ── Lint / Format ──────────────────────────────────────────────────────
lint:
	ruff check backend/src/ admin/src/ ai/src/ tests/

format:
	ruff format backend/src/ admin/src/ ai/src/ tests/

# ── Backend migrations ─────────────────────────────────────────────────
migrate:
	$(ALEMBIC_BACKEND) upgrade head

migrate-gen:
	@test -n "$(name)" || (echo 'Usage: make migrate-gen name="describe_change"' && exit 1)
	$(ALEMBIC_BACKEND) revision --autogenerate -m "$(name)"

migrate-down:
	$(ALEMBIC_BACKEND) downgrade -1

# ── Admin migrations (alias — schema owned by backend Alembic) ─────────
admin-migrate:
	$(ALEMBIC_BACKEND) upgrade head

admin-migrate-gen:
	@echo "Admin schema revisions live under backend/src/infrastructure/database/migrations/versions/"
	@echo "Add a hand-written revision there, or use: make migrate-gen name=\"...\" for backend-owned tables."
	@exit 1

admin-migrate-down:
	$(ALEMBIC_BACKEND) downgrade -1

# ── Seed ───────────────────────────────────────────────────────────────
seed:
	python admin/scripts/seed_initial_admin.py
