# Architecture

## 1. System context

```
                    ┌─────────────────────────────────────────────┐
   Operator /       │   Nginx: React SPA + reverse proxy (:5173)   │
   AI engineer ────▶│   serves the bundle; proxies /api and /ws    │
                    │   to the API service (same-origin, no CORS)  │
                    └───────────────┬─────────────────────────────┘
                                    │ JSON (Bearer JWT) + WS
                    ┌───────────────▼─────────────────────────────┐
   External agents  │              FastAPI application             │
   (A2A) ──────────▶│  /api/v1  ·  /ws/runs/{id}  ·  /metrics      │
   MCP clients ────▶│  auth · RBAC · policy · domain services      │
                    └───┬─────────────┬──────────────┬────────────┘
                        │             │              │
                  ┌─────▼────┐  ┌─────▼─────┐  ┌─────▼──────┐
                  │PostgreSQL│  │   Redis   │  │   Qdrant   │
                  │ state +  │  │ queue +   │  │  memory    │
                  │ audit    │  │ pub/sub   │  │  vectors   │
                  └──────────┘  └─────┬─────┘  └────────────┘
                                      │ BLPOP
                              ┌───────▼────────┐        ┌──────────────┐
                              │  Run worker(s) │───────▶│ LLM Gateway  │
                              │  bounded exec  │        │ local / OpenAI-
                              │  state machine │        │ compatible   │
                              └────────────────┘        └──────────────┘
```

The API and the worker share the same code image but run as separate
processes. The API never executes workflow logic itself — it validates,
persists and enqueues; the worker owns execution.

## 2. Service boundaries

Every module exposes a typed service boundary, validates its inputs, persists
required state, emits audit/telemetry where applicable, and returns explicit
success/failure states.

| Boundary | Module | Responsibility |
| --- | --- | --- |
| Authentication / RBAC | `app.services.auth`, `app.core.security`, `app.api.deps` | Registration, login, JWT issue/verify, role checks, invitations |
| Organizations / projects | `app.services.domain` | Tenant and project lifecycle, tenant-scoped access |
| Agent registry | `app.services.domain` | Agents, immutable version records, publish workflow |
| Tool registry | `app.services.domain` | Tools, risk levels, per-agent permissions (default deny) |
| Workflow builder | `app.services.domain`, `app.services.validation` | Workflow registry, DAG validation (unique ids, resolvable deps, acyclic) |
| Run orchestrator | `app.services.runs`, `app.services.execution` | Run creation, idempotency, state machine, task fan-out |
| Execution workers | `app.worker`, `app.services.execution` | Bounded parallel execution, timeouts, retries, cancellation |
| Policy engine | `app.services.execution` (tool gateway) | Default-deny authorization, high-risk approval interception |
| Human approval | `app.api.v1.routes.approvals` | Pause/resume runs on an authorized decision |
| Memory service | `app.services.memory` | Tenant/project-scoped vector upsert and semantic search |
| Evaluation service | `app.services.evaluation` | Dataset scoring, per-case results, regression gates |
| LLM gateway | `app.services.llm` | Provider abstraction (local deterministic + OpenAI-compatible) |
| Events / observability | `app.services.events`, `app.core.logging`, `app.middleware` | Run lifecycle events (Redis + persisted), structured logs, correlation IDs, OTel |
| Audit trail | `app.services.audit`, `app.api.v1.routes.audit` | Append-only security-relevant event log |
| Reports | `app.api.v1.routes.reports` | Organization-level rollups |
| Protocols | `app.api.v1.routes.mcp`, `app.api.v1.routes.a2a` | Governed MCP JSON-RPC gateway, A2A agent card + task contract |

## 3. Request lifecycle

1. `CorrelationIdMiddleware` assigns or propagates `X-Correlation-ID` and binds
   it to the structured-logging context for the duration of the request.
2. CORS is applied for the configured `CORS_ORIGINS`.
3. The route's dependencies resolve: `Db` opens an `AsyncSession`; `Claims`
   decodes and verifies the Bearer JWT; `UserDep` / `ProjectDep` load and
   tenant-scope the subject.
4. The handler calls a domain service. Services own all database access through
   the repository/session layer — route handlers contain no raw SQL beyond
   simple scoped `select`s.
5. Pydantic v2 response models serialise the result. Errors are raised as
   `HTTPException` and returned as a consistent envelope (see
   [api.md](api.md#error-envelope)).

## 4. Run state machine

```
             enqueue                 worker picks up
  (created) ─────────▶ QUEUED ───────────────────▶ RUNNING
                                                     │
                 ┌───────────────┬──────────────────┼───────────────┐
                 ▼               ▼                   ▼               ▼
          WAITING_APPROVAL   TIMED_OUT           FAILED         SUCCEEDED
                 │
        approval decision
                 │  approved → QUEUED (resume)     rejected → FAILED
```

- **Bounded concurrency.** Within a run, independent nodes execute together
  under an `asyncio.Semaphore(MAX_CONCURRENCY)`; dependent nodes wait for their
  predecessors. The worker never creates unbounded tasks.
- **Timeouts.** Each agent call is wrapped in `asyncio.wait_for(...,
  RUN_TIMEOUT_SECONDS)`. A breach transitions the task to `TIMED_OUT` and the
  run to `TIMED_OUT`.
- **Idempotency.** A run may carry an `idempotency_key`; a repeated submission
  with the same key returns the original run instead of creating a new one
  (enforced by a unique constraint and a pre-check).
- **Cancellation.** `POST /runs/{id}/cancel` sets `CANCELLED`; the executor
  checks run status between scheduling rounds and each node checks on entry.
- **Events.** Every transition publishes to `agentic:run:{id}` (Redis pub/sub,
  consumed by `WS /ws/runs/{id}`) and is persisted to `run_events` for
  after-the-fact retrieval via `GET /runs/{id}/events`.

## 5. Policy: default-deny tool gateway

```
node has tool_id?
   └─ yes ─▶ node has agent_id? ── no ──▶ PermissionError (task fails)
              └─ yes ─▶ ToolPermission(agent, tool, allowed=true)?
                          └─ no ──▶ PermissionError (denied, task fails)
                          └─ yes ─▶ tool.risk_level == "high"?
                                     └─ yes ─▶ Approval exists & approved?
                                                └─ no ──▶ create pending Approval,
                                                          emit APPROVAL_REQUIRED,
                                                          run → WAITING_APPROVAL
                                                └─ yes ─▶ execute
                                     └─ no ──▶ execute
```

Model output is never an authority: an LLM response cannot grant a permission
or release an approval. Tool HTTP endpoints are further constrained by
`TOOL_ALLOWED_HOSTS` (default-deny host allowlist) and bounded retries.

## 6. Data model

Core tables (all UUID primary keys, `created_at` / `updated_at` where relevant,
tenant/organization scope where applicable):

```
organizations ──< users
      │      └──< invitations
      └──< projects ──< agents ──< agent_versions
                   │        └──< tool_permissions >── tools
                   ├──< tools
                   ├──< workflows ──< workflow_versions
                   ├──< memory (Qdrant, keyed by org+project+key)
                   └──< evaluations ──< evaluation_runs ──< evaluation_case_results
                                  └──< regression_gates
projects ──< runs ──< run_tasks
              ├──< run_events
              └──< approvals >── organizations
organizations ──< audit_events
```

Schema is managed by a single consolidated Alembic baseline
(`0001_initial_schema`); see [backend.md](backend.md#database-and-migrations).

## 7. Technology

| Layer | Choice |
| --- | --- |
| API | Python 3.12, FastAPI, Pydantic v2, async I/O |
| Persistence | SQLAlchemy 2.x (async), Alembic, PostgreSQL 16 |
| Coordination | Redis 7 (durable list queue + pub/sub) |
| Vectors | Qdrant 1.15 |
| Orchestration | `asyncio` TaskGroup/gather with a bounded semaphore and an explicit state machine |
| Frontend | React 19, TypeScript, Vite 7, React Router 6 |
| Telemetry | structlog JSON logs, OpenTelemetry (FastAPI + SQLAlchemy), Prometheus client |
| Packaging | Docker Compose (local), Kubernetes manifests in `k8s/` |
