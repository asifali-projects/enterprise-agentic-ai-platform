# Requirements traceability

This maps the source Product Requirements Document to where each requirement is
implemented and verified.

## Functional requirements

| # | Requirement | Implementation | Verified by |
| --- | --- | --- | --- |
| F1 | Authentication / RBAC — typed boundary, input validation, persisted state, audit events, explicit success/failure | `services/auth.py`, `core/security.py`, `api/deps.py` | `test_auth_flow.py`, `test_security.py` |
| F2 | Organizations / projects — tenant-scoped access | `services/domain.py`, `api/deps.py::project` | `test_workflow_and_runs.py::test_cross_tenant_project_access_is_blocked` |
| F3 | Agent registry — versioning, publish | `services/domain.py` (`create_agent`, `create_agent_version`, `publish_agent`) | `test_workflow_and_runs.py` |
| F4 | Tool registry — risk levels, per-agent permissions, default deny | `services/domain.py`, `services/execution.py` (gateway) | scenario AG-003 |
| F5 | Workflow builder — DAG validation, versioning | `services/validation.py`, `services/domain.py::workflow_version` | `test_validation.py`, `test_workflow_and_runs.py::test_workflow_rejects_dependency_cycle` |
| F6 | Run orchestrator — state, timeout, cancellation, retry, auditable outcome | `services/runs.py`, `services/execution.py` | `test_workflow_and_runs.py::test_run_lifecycle_and_events` |
| F7 | Memory service — typed boundary, tenant scope | `services/memory.py`, `api/v1/routes/memory.py` | manual / scenario AG-007 |
| F8 | Policy engine — least privilege, default deny, high-impact approval | `services/execution.py` | scenario AG-003, AG-004 |
| F9 | Human approval — pause/resume, actor + timestamp, expiry, reject unauthorized | `api/v1/routes/approvals.py` | scenario AG-004 |
| F10 | Execution workers — bounded concurrency, stateless, lifecycle events | `worker.py`, `services/execution.py` | scenario AG-005, AG-008 |
| F11 | Evaluation service — datasets, per-case scoring, persisted runs, regression gate | `services/evaluation.py`, `api/v1/routes/evaluations.py` | `test_protocols.py`, scenario AG-006 |
| F12 | Observability — correlation IDs, structured logs, OTel, health | `middleware.py`, `core/logging.py`, `main.py::setup_otel` | `test_health.py` |
| F13 | Audit trail — append-only, actor/resource/timestamp | `services/audit.py`, `api/v1/routes/audit.py` | `test_auth_flow.py` (events created on register) |
| F14 | Reports — organization rollups | `api/v1/routes/reports.py`, `dashboard.py` | manual |

## API contract

All contract endpoints from the PRD are present; see
[../technical/api.md](../technical/api.md). Runs are addressable both top-level
(`/api/v1/runs/{id}` and `/events`, `/cancel`) and project-scoped.

## Non-functional requirements

| Area | Requirement | How it is met |
| --- | --- | --- |
| Architecture | Production-grade, layered | UI / API / orchestration / data / provider / infra are separate modules and processes |
| Secrets | No hard-coded credentials or provider config | `pydantic-settings`; `.env` / secret manager only; verified — no secrets in the image or the frontend bundle |
| Provider neutrality | Provider abstraction mandatory | `services/llm.py::provider()`; local + OpenAI-compatible adapters behind one interface |
| Determinism | Deterministic validation where possible | Workflow DAG validation, exact/partial evaluation scoring, deterministic local provider and embedding |
| Reliability | State, timeout, cancellation, retry, idempotency for every long-running op | Run/task state machine, `asyncio.wait_for`, cancel endpoint, bounded retries, idempotency keys |
| Concurrency | Bounded, never unbounded tasks | `asyncio.Semaphore(MAX_CONCURRENCY)` in the executor |
| Multi-tenancy | Isolation where multi-tenant concepts exist | Organization-scoped queries everywhere; scoped vector namespaces |
| Observability | Correlation IDs, JSON logs, OTel, health/readiness | `middleware.py`, `core/logging.py`, `setup_otel`, `/health/*`, `/metrics` |
| Deployability | Docker Compose local; Kubernetes-ready | `docker-compose.yml`, `k8s/`, migrations run on start |
| Testability | Unit + integration + contract + scenario + failure + security | `backend/tests/` + CI with Postgres/Redis services |

## Non-goals (respected)

- No hard-coded secrets or provider credentials.
- No uncontrolled external-system actions — tool endpoints are host-allowlisted
  and permission-gated.
- No requirement to use one proprietary LLM provider.
- No fabricated metrics or claims of production scale without benchmarks (see
  [../technical/operations.md#known-limitations](../technical/operations.md#known-limitations)).
