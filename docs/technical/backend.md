# Backend guide

## Layout

```
backend/
  app/
    api/
      deps.py                 typed FastAPI dependencies (Db, Claims, UserDep, ProjectDep, require_roles)
      v1/
        router.py             assembles /api/v1 from the route modules (+ /api/v1/auth/* alias)
        routes/               one module per resource
    core/
      config.py               pydantic-settings; all config from env / .env
      security.py              password hashing (bcrypt), JWT issue/verify, token hashing
      logging.py               structlog JSON configuration
    db/
      base.py                 declarative Base, UUID + timestamp mixins
      models.py               all ORM models
      session.py              async engine + session factory
    middleware.py             correlation-id middleware
    schemas/api.py            request/response models incl. Node/Definition
    services/                 domain logic (see below)
    worker.py                 run-queue consumer
  alembic/                    migrations (single baseline)
  tests/                      pytest suite
  conftest.py                 makes `app` importable from the repo root and the image
```

## Services

| Module | Purpose |
| --- | --- |
| `services/auth.py` | `register`, `login`, `create_invitation`, slug generation, audit emission |
| `services/domain.py` | projects, agents, agent versions, tools, tool permissions, workflows, workflow versions; workflow definition parsed to `Definition` and validated |
| `services/validation.py` | `validate_definition` — unique node ids, resolvable dependencies, acyclic (Kahn) |
| `services/runs.py` | `create_run` (idempotency, version resolution, task fan-out), `run_for_org`, `cancel_run`, `list_events` |
| `services/execution.py` | worker-side execution: bounded parallel scheduling, per-node tool gateway + approval interception, timeouts, retries, terminal transitions |
| `services/queue.py` | Redis list queue (`RPUSH` / `BLPOP`) |
| `services/events.py` | `publish` → Redis pub/sub + best-effort persist to `run_events` |
| `services/llm.py` | `provider()` returns the configured LLM adapter (`local` deterministic or OpenAI-compatible) |
| `services/memory.py` | Qdrant collection management, deterministic local embedding, tenant/project-filtered search |
| `services/evaluation.py` | `run_evaluation` — per-case scoring, regression-gate comparison, persisted `evaluation_runs` |
| `services/audit.py` | `audit(...)` appends an `audit_events` row |

## Conventions

- **Async everywhere.** All I/O is `async`; the worker bounds concurrency with a
  semaphore and never launches unbounded tasks.
- **Tenant scoping.** Reads are always filtered by the organization id from the
  verified JWT (`Claims["org_id"]`). `ProjectDep` 404s on a project outside the
  caller's organization.
- **Errors.** Raise `fastapi.HTTPException` with a plain-language message. The
  frontend turns the response envelope into field-level and form-level errors.
- **No raw SQL in routes.** Route handlers use scoped `select(...)`; anything
  with business rules lives in a service.

## Database and migrations

The schema is one consolidated baseline, `0001_initial_schema`, which
materialises every table from `Base.metadata`. This replaced an earlier tangle
of branched/merged revisions that could not be applied to a fresh database.

```bash
# apply (the api container also runs this automatically on start)
docker compose exec api alembic upgrade head

# create a follow-up migration after changing models
docker compose exec api alembic revision --autogenerate -m "add X"
```

`alembic/env.py` reads `DATABASE_URL` from settings and imports `app.db.models`
so autogenerate sees the full metadata.

## Testing

```bash
docker compose exec api pytest -q          # in the container
pytest -q backend/tests                     # from the repo root (needs Postgres + Redis)
```

| File | Covers |
| --- | --- |
| `test_health.py` | liveness, version endpoints |
| `test_security.py` | JWT round-trip |
| `test_validation.py` | workflow DAG validation (valid / cycle / missing dependency) |
| `test_protocols.py` | evaluation scoring function |
| `test_protocol_contracts.py` | A2A agent card, MCP discovery |
| `test_auth_flow.py` | register → `/me`, `/auth/*` alias, duplicate email, bad password, short-password field error, auth required, invite |
| `test_workflow_and_runs.py` | dependency-cycle rejection, full run lifecycle + persisted events, run without a published version, cross-tenant isolation |

Integration tests use `httpx.ASGITransport` against the real app and the
configured PostgreSQL/Redis (Compose locally, service containers in CI). The
pytest event loop is session-scoped so the module-level async engine stays
bound to one loop.

## Type checking

`mypy backend/app` runs in CI as an **advisory** step. The project uses a
pragmatic mypy baseline (`ignore_missing_imports`, no forced annotations) rather
than `strict = true`, because the FastAPI dependency-injection surface and the
inherited route style produce a large number of low-value `strict` findings.
New modules (`services/runs.py`, `services/events.py`, `api/v1/routes/run_index.py`)
are written with full annotations; the intent is to tighten `mypy` module by
module and eventually restore `strict`.

## Lint & format

```bash
ruff check backend/app backend/tests
ruff format backend/app backend/tests
```

Both run in CI as blocking steps. `ruff format` enforces a single consistent
style; the whole backend was reformatted from its original single-line style.
